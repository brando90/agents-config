#!/usr/bin/env python3
"""Keep every committed slide deck readable inside Cursor / VS Code.

TLDR: for each `*.pptx` (and `*.key`) this writes two sibling derivatives that are
always regenerated from the deck -- `<deck>.pdf` (rendered, opens inline in Cursor via
the `tomoki1207.pdf` extension) and `<deck>.pptx.md` (slide-by-slide text outline, so
the deck is greppable and its diffs are readable in git). `--check` exits non-zero when
a derivative is missing or stale, which is what the pre-commit hook and CI use.

Naming: derivatives keep the FULL source filename and append an extension, e.g.
    "Thesis Plan.pptx"  ->  "Thesis Plan.pptx.pdf"  +  "Thesis Plan.pptx.md"
That makes the derivation unambiguous, survives filenames with spaces/parens/trailing
spaces, and lets a repo un-ignore all of them with one `.gitignore` line:
    !**/*.pptx.pdf
    !**/*.key.pdf

Staleness is tracked by the sha256 of the source deck, recorded in the `.md` header.
Git does not preserve mtimes, so mtime comparison is unreliable after a fresh clone;
the recorded hash is.

Dependencies: Python standard library only (a .pptx is a zip of XML). PDF rendering
needs LibreOffice (`soffice`, preferred) or, on macOS, Keynote via AppleScript.

Usage:
    sync_slide_decks.py                      # sync every deck under the git repo root
    sync_slide_decks.py path/to/deck.pptx    # sync specific decks
    sync_slide_decks.py --check              # verify freshness, no writes (exit 1 if stale)
    sync_slide_decks.py --md-only            # skip PDF rendering (no LibreOffice needed)
    sync_slide_decks.py --install-hook       # install the repo's pre-commit hook
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

DECK_SUFFIXES = {".pptx", ".key", ".ppt", ".odp"}
# Only .pptx can be text-dumped with the standard library; .key is a proprietary
# binary (IWA) bundle and .ppt/.odp are out of scope for the text outline.
TEXT_DUMPABLE = {".pptx"}

HASH_MARKER = "source-sha256:"

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

SOFFICE_CANDIDATES = [
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/opt/homebrew/bin/soffice",
]


# ---------------------------------------------------------------- discovery


def repo_root(start: Path) -> Path:
    try:
        out = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return start


def find_decks(root: Path) -> list[Path]:
    decks = []
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            if name.startswith("~$"):  # Office lock file
                continue
            if Path(name).suffix.lower() in DECK_SUFFIXES:
                decks.append(Path(dirpath) / name)
    return sorted(decks)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def derivative_paths(deck: Path) -> tuple[Path, Path | None]:
    """Return (pdf_path, md_path_or_None) for a deck."""
    pdf = deck.with_name(deck.name + ".pdf")
    md = deck.with_name(deck.name + ".md") if deck.suffix.lower() in TEXT_DUMPABLE else None
    return pdf, md


def legacy_siblings(deck: Path) -> list[Path]:
    """Hand-exported companions from before this convention: `<stem>.pdf` / `<stem>.txt`
    next to `<stem>.pptx`. They are indistinguishable from an unrelated file and nothing
    keeps them in sync, so they are reported for removal rather than trusted."""
    stem = deck.stem.rstrip()
    found = []
    for suffix in (".pdf", ".txt"):
        for candidate in {deck.with_name(deck.stem + suffix), deck.with_name(stem + suffix)}:
            if candidate.exists() and candidate not in found:
                found.append(candidate)
    return found


def recorded_hash(md: Path) -> str | None:
    if not md.exists():
        return None
    try:
        head = md.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    m = re.search(re.escape(HASH_MARKER) + r"\s*`?([0-9a-f]{64})`?", head)
    return m.group(1) if m else None


# ---------------------------------------------------------- pptx text dump


def _para_text(para: ET.Element) -> str:
    """Concatenate the text runs of one <a:p>, including fields and line breaks."""
    parts = []
    for node in para.iter():
        tag = node.tag.split("}")[-1]
        if tag == "t":
            parts.append(node.text or "")
        elif tag == "br":
            parts.append(" ")
    return "".join(parts).strip()


def _para_level(para: ET.Element) -> int:
    ppr = para.find("a:pPr", NS)
    if ppr is None:
        return 0
    try:
        return int(ppr.get("lvl", "0"))
    except ValueError:
        return 0


def _txbody_lines(txbody: ET.Element) -> list[tuple[int, str]]:
    lines = []
    for para in txbody.findall("a:p", NS):
        text = _para_text(para)
        if text:
            lines.append((_para_level(para), text))
    return lines


def _is_title(shape: ET.Element) -> bool:
    ph = shape.find("./p:nvSpPr/p:nvPr/p:ph", NS)
    return ph is not None and ph.get("type") in {"title", "ctrTitle"}


def _table_rows(tbl: ET.Element) -> list[list[str]]:
    rows = []
    for tr in tbl.findall("a:tr", NS):
        cells = []
        for tc in tr.findall("a:tc", NS):
            body = tc.find("a:txBody", NS)
            cell = " / ".join(t for _, t in _txbody_lines(body)) if body is not None else ""
            cells.append(cell.replace("|", "\\|"))
        rows.append(cells)
    return rows


def _walk_shapes(tree: ET.Element):
    """Yield (kind, element) for shapes in document order, descending into groups."""
    sptree = tree.find("./p:cSld/p:spTree", NS)
    if sptree is None:
        return

    def walk(parent):
        for child in parent:
            tag = child.tag.split("}")[-1]
            if tag == "sp":
                yield ("sp", child)
            elif tag == "grpSp":
                yield from walk(child)
            elif tag == "graphicFrame":
                for tbl in child.iter("{%s}tbl" % NS["a"]):
                    yield ("tbl", tbl)
            elif tag == "pic":
                yield ("pic", child)

    yield from walk(sptree)


def slide_order(zf: zipfile.ZipFile) -> list[str]:
    """Slide part names in presentation order; falls back to numeric filename sort."""
    try:
        pres = ET.fromstring(zf.read("ppt/presentation.xml"))
        rels = ET.fromstring(zf.read("ppt/_rels/presentation.xml.rels"))
        id_to_target = {
            rel.get("Id"): rel.get("Target") for rel in rels.findall("rel:Relationship", NS)
        }
        ordered = []
        for sld_id in pres.findall("./p:sldIdLst/p:sldId", NS):
            rid = sld_id.get("{%s}id" % NS["r"])
            target = id_to_target.get(rid)
            if not target:
                continue
            name = os.path.normpath(os.path.join("ppt", target)).replace(os.sep, "/")
            if name in zf.namelist():
                ordered.append(name)
        if ordered:
            return ordered
    except (KeyError, ET.ParseError):
        pass
    names = [n for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    return sorted(names, key=lambda n: int(re.search(r"(\d+)", os.path.basename(n)).group(1)))


def notes_for(zf: zipfile.ZipFile, slide_part: str) -> str:
    """Speaker notes for a slide, via its part relationships."""
    rels_name = f"{os.path.dirname(slide_part)}/_rels/{os.path.basename(slide_part)}.rels"
    if rels_name not in zf.namelist():
        return ""
    try:
        rels = ET.fromstring(zf.read(rels_name))
    except ET.ParseError:
        return ""
    for rel in rels.findall("rel:Relationship", NS):
        if rel.get("Type", "").endswith("/notesSlide"):
            target = os.path.normpath(
                os.path.join(os.path.dirname(slide_part), rel.get("Target"))
            ).replace(os.sep, "/")
            if target not in zf.namelist():
                return ""
            try:
                tree = ET.fromstring(zf.read(target))
            except ET.ParseError:
                return ""
            lines = []
            for kind, shape in _walk_shapes(tree):
                if kind != "sp":
                    continue
                ph = shape.find("./p:nvSpPr/p:nvPr/p:ph", NS)
                if ph is None or ph.get("type") != "body":
                    continue
                body = shape.find("p:txBody", NS)
                if body is not None:
                    lines += [t for _, t in _txbody_lines(body)]
            return "\n".join(lines).strip()
    return ""


def pptx_to_markdown(deck: Path, digest: str) -> str:
    with zipfile.ZipFile(deck) as zf:
        parts = slide_order(zf)
        out = [
            f"# {deck.name} — slide text",
            "",
            "**TLDR:** Auto-generated slide-by-slide text outline of the deck next to this file,",
            "so the deck is readable, greppable and diffable inside Cursor. **Do not edit by hand**",
            f"— edit the `.pptx` and re-run `~/agents-config/scripts/sync_slide_decks.py`.",
            "",
            f"- source: `{deck.name}`",
            f"- {HASH_MARKER} `{digest}`",
            f"- slides: {len(parts)}",
            f"- rendered PDF: `{deck.name}.pdf`",
            f"- generator: `~/agents-config/scripts/sync_slide_decks.py`",
            "",
            "---",
            "",
        ]
        for idx, part in enumerate(parts, start=1):
            try:
                tree = ET.fromstring(zf.read(part))
            except ET.ParseError:
                out += [f"## Slide {idx}", "", "_(unparseable slide XML)_", ""]
                continue

            title = ""
            body_blocks: list[str] = []
            n_pics = 0
            for kind, shape in _walk_shapes(tree):
                if kind == "pic":
                    n_pics += 1
                    continue
                if kind == "tbl":
                    rows = _table_rows(shape)
                    if not rows:
                        continue
                    width = max(len(r) for r in rows)
                    rows = [r + [""] * (width - len(r)) for r in rows]
                    block = ["| " + " | ".join(rows[0]) + " |",
                             "|" + "|".join([" --- "] * width) + "|"]
                    block += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                    body_blocks.append("\n".join(block))
                    continue
                body = shape.find("p:txBody", NS)
                if body is None:
                    continue
                lines = _txbody_lines(body)
                if not lines:
                    continue
                if not title and _is_title(shape):
                    title = " ".join(t for _, t in lines)
                    continue
                body_blocks.append(
                    "\n".join(f"{'  ' * lvl}- {text}" for lvl, text in lines)
                )

            out.append(f"## Slide {idx}" + (f" — {title}" if title else ""))
            out.append("")
            for block in body_blocks:
                out.append(block)
                out.append("")
            if n_pics:
                out.append(f"_({n_pics} image{'s' if n_pics != 1 else ''} on this slide)_")
                out.append("")
            note = notes_for(zf, part)
            if note:
                out.append("> **Speaker notes:** " + note.replace("\n", "\n> "))
                out.append("")
    return "\n".join(out).rstrip() + "\n"


# ------------------------------------------------------------- pdf render


def find_soffice() -> str | None:
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for cand in SOFFICE_CANDIDATES:
        if Path(cand).exists():
            return cand
    return None


def render_pdf_soffice(deck: Path, dest: Path, soffice: str) -> None:
    """LibreOffice headless render. Uses a scratch user profile so it never fights a
    running GUI instance, and a scratch outdir because soffice picks its own filename."""
    with tempfile.TemporaryDirectory(prefix="deck-pdf-") as tmp:
        profile = Path(tmp) / "profile"
        outdir = Path(tmp) / "out"
        outdir.mkdir()
        cmd = [
            soffice,
            f"-env:UserInstallation=file://{profile}",
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(outdir),
            str(deck),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        produced = sorted(outdir.glob("*.pdf"))
        if not produced:
            raise RuntimeError(
                f"LibreOffice produced no PDF for {deck.name}\n"
                f"stdout: {proc.stdout.strip()}\nstderr: {proc.stderr.strip()}"
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced[0]), str(dest))


KEYNOTE_SCRIPT = """
on run argv
  set inPath to item 1 of argv
  set outPath to item 2 of argv
  tell application "Keynote"
    launch
    repeat until it is running
      delay 0.2
    end repeat
    set doc to open (POSIX file inPath)
    delay 1
    export doc to (POSIX file outPath) as PDF with properties {export style:IndividualSlides, ¬
      all stages:false, skipped slides:false, PDF image quality:Best}
    close doc saving no
  end tell
end run
"""


def render_pdf_keynote(deck: Path, dest: Path) -> None:
    """macOS fallback: drive Keynote via AppleScript. Needs Automation permission and
    briefly opens the GUI, so it is only used when LibreOffice is absent."""
    if sys.platform != "darwin":
        raise RuntimeError("Keynote fallback is macOS-only")
    if not Path("/Applications/Keynote.app").exists():
        raise RuntimeError("Keynote.app not found")
    with tempfile.NamedTemporaryFile("w", suffix=".applescript", delete=False) as fh:
        fh.write(KEYNOTE_SCRIPT)
        script = fh.name
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        proc = subprocess.run(
            ["osascript", script, str(deck.resolve()), str(dest.resolve())],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if not dest.exists():
            raise RuntimeError(
                f"Keynote produced no PDF for {deck.name}\n"
                f"stdout: {proc.stdout.strip()}\nstderr: {proc.stderr.strip()}"
            )
    finally:
        os.unlink(script)


def render_pdf(deck: Path, dest: Path, soffice: str | None) -> str:
    if soffice:
        render_pdf_soffice(deck, dest, soffice)
        return "libreoffice"
    render_pdf_keynote(deck, dest)
    return "keynote"


# ------------------------------------------------------------------ hook


PRE_COMMIT_HOOK = """#!/bin/sh
# Installed by ~/agents-config/scripts/sync_slide_decks.py --install-hook
# Refuses a commit whose slide-deck PDFs / text dumps are stale (agents-config
# Trigger Rule 40). Run the syncer and stage the derivatives to proceed.
if git diff --cached --name-only --diff-filter=ACM | grep -qiE '\\.(pptx|key|ppt|odp)$'; then
    python3 "$HOME/agents-config/scripts/sync_slide_decks.py" --check || exit 1
fi
"""


def install_hook(root: Path) -> Path:
    hook = root / ".git" / "hooks" / "pre-commit"
    if hook.exists():
        existing = hook.read_text(encoding="utf-8", errors="replace")
        if "sync_slide_decks.py" in existing:
            return hook
        hook.write_text(existing.rstrip() + "\n\n" + PRE_COMMIT_HOOK.split("\n", 1)[1])
    else:
        hook.write_text(PRE_COMMIT_HOOK)
    hook.chmod(0o755)
    return hook


# ------------------------------------------------------------------ main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="*", type=Path, help="decks or directories (default: repo root)")
    ap.add_argument("--check", action="store_true", help="verify freshness, write nothing")
    ap.add_argument("--force", action="store_true", help="regenerate even if up to date")
    ap.add_argument("--md-only", action="store_true", help="skip PDF rendering")
    ap.add_argument("--pdf-only", action="store_true", help="skip the markdown text dump")
    ap.add_argument("--install-hook", action="store_true", help="install the pre-commit hook")
    args = ap.parse_args()

    cwd = Path.cwd()
    root = repo_root(cwd)

    if args.install_hook:
        hook = install_hook(root)
        print(f"pre-commit hook installed: {hook}")
        if not args.paths and not args.check:
            return 0

    decks: list[Path] = []
    targets = args.paths or [root]
    for target in targets:
        target = target if target.is_absolute() else (cwd / target)
        if target.is_dir():
            decks += find_decks(target)
        elif target.suffix.lower() in DECK_SUFFIXES:
            decks.append(target)
        else:
            print(f"skip (not a deck): {target}", file=sys.stderr)
    decks = sorted(set(decks))

    if not decks:
        print("no slide decks found")
        return 0

    soffice = None if args.md_only else find_soffice()
    if not args.md_only and not args.check and soffice is None and sys.platform != "darwin":
        print(
            "error: no PDF renderer. Install LibreOffice (`brew install --cask libreoffice`\n"
            "or your distro's `libreoffice`), or pass --md-only.",
            file=sys.stderr,
        )
        return 2

    stale: list[str] = []
    legacy: list[str] = []
    synced = 0
    for deck in decks:
        digest = sha256_of(deck)
        pdf, md = derivative_paths(deck)
        rel = deck.relative_to(root) if deck.is_relative_to(root) else deck

        for old in legacy_siblings(deck):
            if old not in (pdf, md):
                legacy.append(f"  {old.relative_to(root) if old.is_relative_to(root) else old}")

        want_md = md is not None and not args.pdf_only
        want_pdf = not args.md_only

        md_fresh = (not want_md) or (recorded_hash(md) == digest)
        pdf_fresh = (not want_pdf) or pdf.exists()
        # A .key has no text dump to carry the hash, so its PDF freshness cannot be
        # verified from content -- existence is the best available signal.
        if want_pdf and want_md and not md_fresh:
            pdf_fresh = False

        if args.check:
            if not md_fresh:
                stale.append(f"  {rel}: text dump missing or stale ({md.name})")
            if not pdf_fresh:
                stale.append(f"  {rel}: rendered PDF missing or stale ({pdf.name})")
            continue

        if md_fresh and pdf_fresh and not args.force:
            print(f"up to date: {rel}")
            continue

        if want_md and (args.force or not md_fresh):
            md.write_text(pptx_to_markdown(deck, digest), encoding="utf-8")
            print(f"wrote text dump: {md.relative_to(root) if md.is_relative_to(root) else md}")

        if want_pdf and (args.force or not pdf_fresh):
            try:
                engine = render_pdf(deck, pdf, soffice)
            except Exception as exc:  # noqa: BLE001 - report and keep going
                print(f"error rendering {rel}: {exc}", file=sys.stderr)
                return 3
            size = pdf.stat().st_size
            print(
                f"wrote PDF ({engine}, {size / 1e6:.1f} MB): "
                f"{pdf.relative_to(root) if pdf.is_relative_to(root) else pdf}"
            )
        synced += 1

    if legacy:
        print(
            "\nnote: hand-exported companions found next to a deck. Nothing keeps these in\n"
            "sync with the deck, so review and `git rm` them once the generated\n"
            "`<deck>.pptx.pdf` / `<deck>.pptx.md` are committed:",
            file=sys.stderr,
        )
        for line in legacy:
            print(line, file=sys.stderr)

    if args.check:
        if stale:
            print("stale slide-deck derivatives (agents-config Trigger Rule 40):", file=sys.stderr)
            for line in stale:
                print(line, file=sys.stderr)
            print(
                "\nfix: python3 ~/agents-config/scripts/sync_slide_decks.py "
                "&& git add the regenerated .pdf/.md",
                file=sys.stderr,
            )
            return 1
        print(f"all {len(decks)} slide deck(s) in sync")
        return 0

    print(f"\nsynced {synced} of {len(decks)} deck(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
