#!/usr/bin/env python3
"""Keep every committed slide deck readable inside Cursor / VS Code.

TLDR: for each slide deck this writes sibling derivatives that are always regenerated
from the deck -- `<deck>.pdf` (rendered, opens inline in Cursor via the `tomoki1207.pdf`
extension) and, for `.pptx`, `<deck>.pptx.md` (slide-by-slide text outline, so the deck
is greppable and its git diff is readable instead of "Binary files differ"). A manifest
records the sha256 of the deck *and* of each derivative, so `--check` cannot be fooled
into passing on stale output; `--check-staged` applies the same gate to git's index and
is what the installed pre-commit hook runs.

Naming: derivatives keep the FULL source filename and append an extension, e.g.
    "Thesis Plan.pptx"  ->  "Thesis Plan.pptx.pdf"  +  "Thesis Plan.pptx.md"
That makes the derivation unambiguous, survives filenames with spaces/parens/em-dashes
/trailing spaces, and lets a repo un-ignore all of them with one `.gitignore` line:
    !**/*.pptx.pdf
(Keep deck extensions lowercase: a case-sensitive repo would still ignore `.PPTX.pdf`.)

Freshness lives in `.slide-sync.json` at the repo root, NOT in mtimes and NOT only in
the `.md` header. Three reasons:
  - git does not preserve mtimes, so after a fresh clone every derivative looks newer
    than its source and an mtime check silently passes on stale files;
  - a `.pdf` cannot carry a provenance header, and `.key`/`.ppt`/`.odp` have no text
    dump at all, so the `.md` header alone leaves those unverifiable;
  - each derivative's own hash is recorded too, which catches a truncated, replaced or
    half-written file, and a manifest entry is written only AFTER that derivative is
    produced successfully -- so a failed render cannot leave a passing state behind.

Dependencies: Python 3.8+ standard library only (a .pptx is a zip of XML). Rendering
needs LibreOffice (`soffice`, preferred) or, on macOS, Keynote via AppleScript.

Usage:
    sync_slide_decks.py                      # sync every deck under the git repo root
    sync_slide_decks.py path/to/deck.pptx    # sync specific decks
    sync_slide_decks.py --check              # verify the working tree (exit 1 if stale)
    sync_slide_decks.py --check-staged       # verify git's index (the pre-commit gate)
    sync_slide_decks.py --md-only            # skip rendering (no LibreOffice needed)
    sync_slide_decks.py --install-hook       # install the pre-commit hook
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

DECK_SUFFIXES = {".pptx", ".key", ".ppt", ".odp"}
# Only .pptx can be text-dumped with the standard library: .key is a proprietary binary
# (IWA) bundle, and .ppt / .odp are different container formats. Those still get a
# rendered PDF and full manifest-tracked freshness -- they just have no text sibling.
TEXT_DUMPABLE = {".pptx"}

MANIFEST_NAME = ".slide-sync.json"
MANIFEST_VERSION = 1
HASH_MARKER = "source-sha256:"
HOOK_HELPER_NAME = "slide-deck-sync-check"

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

FIX_HINT = (
    "fix: python3 ~/agents-config/scripts/sync_slide_decks.py "
    f"&& git add the deck, its .pdf/.md siblings and {MANIFEST_NAME}"
)


class DeckError(RuntimeError):
    """A deck could not be parsed or rendered. Never swallowed into a passing state."""


# ------------------------------------------------------------------- git / paths


def git(root: Path, *args: str, binary: bool = False, check: bool = True):
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False
    )
    if proc.returncode != 0:
        if check:
            raise RuntimeError(
                f"git {' '.join(args)} failed: {proc.stderr.decode(errors='replace').strip()}"
            )
        return None
    return proc.stdout if binary else proc.stdout.decode("utf-8", errors="replace")


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


def as_rel(path: Path, root: Path) -> str:
    """Repo-relative POSIX path, or an absolute path when the file is outside the repo.
    Avoids Path.is_relative_to so the floor stays at Python 3.8."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_derivatives(deck: Path) -> dict[str, Path]:
    """Canonical derivative set for a deck. Deliberately NOT influenced by --md-only:
    the gate always demands the full set, so a partial sync cannot produce a pass."""
    out = {"pdf": deck.with_name(deck.name + ".pdf")}
    if deck.suffix.lower() in TEXT_DUMPABLE:
        out["md"] = deck.with_name(deck.name + ".md")
    return out


def legacy_siblings(deck: Path) -> list[Path]:
    """Hand-exported companions from before this convention: `<stem>.pdf` / `<stem>.txt`
    next to `<stem>.pptx`. They are indistinguishable from an unrelated file and nothing
    keeps them in sync, so they are reported for removal rather than trusted."""
    generated = set(expected_derivatives(deck).values())
    found: list[Path] = []
    for suffix in (".pdf", ".txt"):
        for candidate in (
            deck.with_name(deck.stem + suffix),
            deck.with_name(deck.stem.rstrip() + suffix),
        ):
            if candidate not in generated and candidate.exists() and candidate not in found:
                found.append(candidate)
    return found


# ---------------------------------------------------------------------- manifest


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_NAME


def load_manifest(root: Path) -> dict:
    path = manifest_path(root)
    if not path.exists():
        return {"version": MANIFEST_VERSION, "generator": Path(__file__).name, "decks": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": MANIFEST_VERSION, "generator": Path(__file__).name, "decks": {}}
    data.setdefault("decks", {})
    return data


def parse_manifest(data: bytes) -> dict:
    try:
        out = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"decks": {}}
    out.setdefault("decks", {})
    return out


def save_manifest(root: Path, manifest: dict) -> None:
    manifest["version"] = MANIFEST_VERSION
    manifest["generator"] = Path(__file__).name
    manifest["decks"] = dict(sorted(manifest["decks"].items()))
    manifest_path(root).write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------- OPC part paths


def resolve_part(base_part: str, target: str) -> str:
    """Resolve an OPC relationship target to a zip part name.

    A target may be package-root-absolute ("/ppt/slides/slide2.xml") or relative to the
    base part's directory ("slides/slide2.xml"). Naive os.path.join lets an absolute
    target swallow the base and keeps its leading slash, which then never matches a zip
    entry -- that silently dropped slides.
    """
    target = target.replace("\\", "/")
    if target.startswith("/"):
        return posixpath.normpath(target).lstrip("/")
    base_dir = posixpath.dirname(base_part)
    return posixpath.normpath(posixpath.join(base_dir, target)).lstrip("/")


def relationships(zf: zipfile.ZipFile, part: str) -> list[dict]:
    """Relationships declared for a part, as {Id, Type, Target, TargetMode} dicts."""
    rels_name = posixpath.join(
        posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels"
    ).lstrip("/")
    if rels_name not in zf.namelist():
        return []
    try:
        tree = ET.fromstring(zf.read(rels_name))
    except ET.ParseError as exc:
        raise DeckError(f"unparseable relationships part {rels_name}: {exc}") from exc
    return [dict(rel.attrib) for rel in tree.findall("rel:Relationship", NS)]


def slide_order(zf: zipfile.ZipFile) -> list[str]:
    """Slide part names in true presentation order.

    Falls back to a numeric filename sort ONLY when the package declares no slide id
    list at all. A declared list that fails to resolve is an error, never a silent
    partial order -- a partial order reorders or omits slides without saying so.
    """
    names = zf.namelist()
    if "ppt/presentation.xml" not in names:
        raise DeckError("not a PowerPoint package: ppt/presentation.xml is missing")
    try:
        pres = ET.fromstring(zf.read("ppt/presentation.xml"))
    except ET.ParseError as exc:
        raise DeckError(f"unparseable ppt/presentation.xml: {exc}") from exc

    sld_ids = pres.findall("./p:sldIdLst/p:sldId", NS)
    if sld_ids:
        by_id = {rel.get("Id"): rel for rel in relationships(zf, "ppt/presentation.xml")}
        ordered = []
        for sld_id in sld_ids:
            rid = sld_id.get("{%s}id" % NS["r"])
            rel = by_id.get(rid)
            if rel is None or rel.get("TargetMode") == "External":
                raise DeckError(f"slide relationship {rid!r} is missing or external")
            part = resolve_part("ppt/presentation.xml", rel.get("Target", ""))
            if part not in names:
                raise DeckError(f"slide relationship {rid!r} points at absent part {part!r}")
            ordered.append(part)
        return ordered

    numeric = [n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    if not numeric:
        raise DeckError("package declares no slides")
    return sorted(numeric, key=lambda n: int(re.search(r"(\d+)", posixpath.basename(n)).group(1)))


# ------------------------------------------------------------- pptx text dump


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


def notes_for(zf: zipfile.ZipFile, slide_part: str) -> str:
    """Speaker notes for a slide, resolved through its part relationships."""
    for rel in relationships(zf, slide_part):
        if not rel.get("Type", "").endswith("/notesSlide"):
            continue
        if rel.get("TargetMode") == "External":
            return ""
        part = resolve_part(slide_part, rel.get("Target", ""))
        if part not in zf.namelist():
            return ""
        try:
            tree = ET.fromstring(zf.read(part))
        except ET.ParseError as exc:
            raise DeckError(f"unparseable notes part {part}: {exc}") from exc
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
    try:
        zf = zipfile.ZipFile(deck)
    except zipfile.BadZipFile as exc:
        raise DeckError(f"not a readable .pptx (zip) file: {exc}") from exc
    with zf:
        parts = slide_order(zf)
        out = [
            f"# {deck.name} — slide text",
            "",
            "**TLDR:** Auto-generated slide-by-slide text outline of the deck next to this file,",
            "so the deck is readable, greppable and diffable inside Cursor. **Do not edit by hand**",
            "— edit the deck and re-run `~/agents-config/scripts/sync_slide_decks.py`.",
            "",
            f"- source: `{deck.name}`",
            f"- {HASH_MARKER} `{digest}`",
            "- slides: %d" % len(parts),
            f"- rendered PDF: `{deck.name}.pdf`",
            f"- freshness gate: `{MANIFEST_NAME}` at the repo root (authoritative)",
            "- generator: `~/agents-config/scripts/sync_slide_decks.py`",
            "",
            "---",
            "",
        ]
        for idx, part in enumerate(parts, start=1):
            try:
                tree = ET.fromstring(zf.read(part))
            except ET.ParseError as exc:
                # Never degrade to a placeholder: that records a fresh hash over a
                # derivative that silently lost a slide's content.
                raise DeckError(f"unparseable slide part {part}: {exc}") from exc

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
                    block = [
                        "| " + " | ".join(rows[0]) + " |",
                        "|" + "|".join([" --- "] * width) + "|",
                    ]
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
                body_blocks.append("\n".join(f"{'  ' * lvl}- {text}" for lvl, text in lines))

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


# ------------------------------------------------------------------ pdf render


def find_soffice() -> str | None:
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for cand in SOFFICE_CANDIDATES:
        if Path(cand).exists():
            return cand
    return None


def soffice_version(soffice: str) -> str:
    try:
        out = subprocess.run(
            [soffice, "--version"], capture_output=True, text=True, timeout=120
        )
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else "libreoffice"
    except (OSError, subprocess.SubprocessError, IndexError):
        return "libreoffice"


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
            raise DeckError(
                f"LibreOffice produced no PDF\n"
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
    """macOS fallback: drive Keynote via AppleScript. Needs Automation permission for the
    calling terminal (System Settings -> Privacy & Security -> Automation); without it
    osascript fails -600 "Application isn't running", which reads like a crash but is a
    permissions denial. Only used when LibreOffice is absent."""
    if sys.platform != "darwin":
        raise DeckError("Keynote fallback is macOS-only")
    if not Path("/Applications/Keynote.app").exists():
        raise DeckError("Keynote.app not found")
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
            raise DeckError(
                "Keynote produced no PDF (grant Automation permission?)\n"
                f"stdout: {proc.stdout.strip()}\nstderr: {proc.stderr.strip()}"
            )
    finally:
        os.unlink(script)


def render_pdf(deck: Path, dest: Path, soffice: str | None) -> str:
    """Render to a scratch file first, then move into place, so a failed render never
    leaves a half-written PDF that a later run could hash as if it were good."""
    with tempfile.TemporaryDirectory(prefix="deck-stage-") as tmp:
        staged = Path(tmp) / "out.pdf"
        if soffice:
            render_pdf_soffice(deck, staged, soffice)
            engine = soffice_version(soffice)
        else:
            render_pdf_keynote(deck, staged)
            engine = "keynote (applescript)"
        if staged.stat().st_size == 0:
            raise DeckError("renderer produced a zero-byte PDF")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged), str(dest))
    return engine


# ----------------------------------------------------------------------- hooks


HOOK_HELPER = """#!/bin/sh
# Installed by ~/agents-config/scripts/sync_slide_decks.py --install-hook
# Refuses a commit whose slide-deck derivatives are missing or stale IN THE INDEX
# (agents-config Trigger Rule 40). Filenames are read NUL-delimited inside the
# checker, so decks whose names contain spaces, em-dashes or quotes are not skipped.
exec python3 "$HOME/agents-config/scripts/sync_slide_decks.py" --check-staged
"""

HOOK_DELEGATE = f'"$(git rev-parse --git-path hooks)"/{HOOK_HELPER_NAME} || exit 1\n'


def hooks_dir(root: Path) -> Path:
    """Effective hooks directory, honouring core.hooksPath and linked worktrees (where
    .git is a file, so root/'.git'/'hooks' does not exist)."""
    out = git(root, "rev-parse", "--git-path", "hooks", check=False)
    if out is None:
        return root / ".git" / "hooks"
    candidate = Path(out.strip())
    return candidate if candidate.is_absolute() else root / candidate


def install_hook(root: Path) -> tuple[Path, str]:
    hdir = hooks_dir(root)
    hdir.mkdir(parents=True, exist_ok=True)
    helper = hdir / HOOK_HELPER_NAME
    helper.write_text(HOOK_HELPER, encoding="utf-8")
    helper.chmod(0o755)

    pre_commit = hdir / "pre-commit"
    if not pre_commit.exists():
        pre_commit.write_text("#!/bin/sh\n" + HOOK_DELEGATE, encoding="utf-8")
        pre_commit.chmod(0o755)
        return helper, "created"

    existing = pre_commit.read_text(encoding="utf-8", errors="replace")
    if HOOK_HELPER_NAME in existing:
        return helper, "already wired"
    # Appending is unsafe: an existing hook that ends in `exit 0` (or any early exit)
    # would leave the appended check unreachable while installation reported success.
    return helper, "manual"


# ------------------------------------------------------------------ check gates


def check_worktree(root: Path, decks: list[Path]) -> list[str]:
    manifest = load_manifest(root)
    entries = manifest.get("decks", {})
    problems: list[str] = []

    for deck in decks:
        rel = as_rel(deck, root)
        entry = entries.get(rel)
        if entry is None:
            problems.append(f"  {rel}: not recorded in {MANIFEST_NAME}")
            continue
        if entry.get("source_sha256") != sha256_of(deck):
            problems.append(f"  {rel}: deck changed since its derivatives were generated")
            continue
        recorded = entry.get("derivatives", {})
        for kind, path in expected_derivatives(deck).items():
            drel = as_rel(path, root)
            info = recorded.get(drel)
            if info is None:
                problems.append(f"  {rel}: {kind} not recorded in {MANIFEST_NAME} ({drel})")
            elif not path.exists():
                problems.append(f"  {rel}: {kind} missing on disk ({drel})")
            elif sha256_of(path) != info.get("sha256"):
                problems.append(f"  {rel}: {kind} modified after generation ({drel})")

    known = {as_rel(d, root) for d in decks}
    for rel in entries:
        if rel not in known and not (root / rel).exists():
            problems.append(f"  {rel}: recorded in {MANIFEST_NAME} but the deck is gone")
    return problems


def staged_paths(root: Path) -> set[str]:
    """Paths in the staged change set, read NUL-delimited so git never quotes or escapes
    a filename (the em-dash quoting is what let decks slip past a shell grep). Renames
    are included -- git mv reports R, which an ACM-only filter silently ignored."""
    out = git(root, "diff", "--cached", "-z", "--name-only", "--diff-filter=ACMRD", check=False)
    if out is None:
        return set()
    return {p for p in out.split("\0") if p}


def index_blob(root: Path, rel: str) -> bytes | None:
    return git(root, "cat-file", "blob", f":{rel}", binary=True, check=False)


def index_decks(root: Path) -> list[str]:
    out = git(root, "ls-files", "-z", check=False)
    if out is None:
        return []
    return sorted(
        p for p in out.split("\0") if p and Path(p).suffix.lower() in DECK_SUFFIXES
    )


def check_staged(root: Path) -> tuple[list[str], bool]:
    """Verify the snapshot being committed, not the working tree. A working-tree check
    passes while the commit itself carries only the deck, or carries a deck that differs
    from the one the derivatives were built from.

    Returns (problems, ran).
    """
    staged = staged_paths(root)
    if not staged:
        return [], False
    relevant = any(
        Path(p).suffix.lower() in DECK_SUFFIXES
        or p == MANIFEST_NAME
        or re.search(r"\.(pptx|key|ppt|odp)\.(pdf|md)$", p, re.IGNORECASE)
        for p in staged
    )
    if not relevant:
        return [], False

    raw = index_blob(root, MANIFEST_NAME)
    decks = index_decks(root)
    if not decks:
        return [], True
    if raw is None:
        return [f"  {MANIFEST_NAME} is not staged, so no deck freshness can be verified"], True

    entries = parse_manifest(raw).get("decks", {})
    problems: list[str] = []
    for rel in decks:
        blob = index_blob(root, rel)
        if blob is None:
            continue
        entry = entries.get(rel)
        if entry is None:
            problems.append(f"  {rel}: not recorded in the staged {MANIFEST_NAME}")
            continue
        if entry.get("source_sha256") != sha256_bytes(blob):
            problems.append(f"  {rel}: staged deck does not match its staged derivatives")
            continue
        recorded = entry.get("derivatives", {})
        for kind, path in expected_derivatives(Path(rel)).items():
            drel = path.as_posix()
            info = recorded.get(drel)
            if info is None:
                problems.append(f"  {rel}: {kind} not recorded in staged {MANIFEST_NAME}")
                continue
            dblob = index_blob(root, drel)
            if dblob is None:
                problems.append(f"  {rel}: {kind} is not staged ({drel})")
            elif sha256_bytes(dblob) != info.get("sha256"):
                problems.append(f"  {rel}: staged {kind} is not the generated one ({drel})")
    return problems, True


# ------------------------------------------------------------------------ main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="*", type=Path, help="decks or directories (default: repo root)")
    ap.add_argument("--check", action="store_true", help="verify the working tree, write nothing")
    ap.add_argument(
        "--check-staged", action="store_true", help="verify git's index (the pre-commit gate)"
    )
    ap.add_argument("--force", action="store_true", help="regenerate even if up to date")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--md-only", action="store_true", help="skip PDF rendering")
    mode.add_argument("--pdf-only", action="store_true", help="skip the markdown text dump")
    ap.add_argument("--install-hook", action="store_true", help="install the pre-commit hook")
    args = ap.parse_args()

    verifying = args.check or args.check_staged
    if verifying and args.install_hook:
        ap.error("--install-hook writes files; it cannot be combined with a check")
    if verifying and (args.md_only or args.pdf_only):
        # A partial check is a false-pass generator: it is exactly how a stale PDF got
        # certified by a fresh .md. The gate always demands the full derivative set.
        ap.error("--check/--check-staged always verify the full derivative set")
    if args.check and args.check_staged:
        ap.error("choose either --check (working tree) or --check-staged (index)")

    cwd = Path.cwd()
    root = repo_root(cwd)

    if args.install_hook:
        helper, how = install_hook(root)
        hdir = helper.parent
        if how == "manual":
            print(
                f"wrote {helper}\n"
                f"An existing {hdir / 'pre-commit'} was left untouched (appending after an\n"
                f"early `exit` would silently disable the check). Add this line to it:\n\n"
                f"    {HOOK_DELEGATE.strip()}\n",
                file=sys.stderr,
            )
        else:
            print(f"pre-commit hook {how}: {hdir / 'pre-commit'} -> {helper.name}")
        if not args.paths:
            return 0

    if args.check_staged:
        problems, ran = check_staged(root)
        if problems:
            print(
                "stale or missing slide-deck derivatives in the commit "
                "(agents-config Trigger Rule 40):",
                file=sys.stderr,
            )
            for line in problems:
                print(line, file=sys.stderr)
            print(f"\n{FIX_HINT}", file=sys.stderr)
            return 1
        if ran:
            print("staged slide decks are in sync")
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

    for deck in decks:
        old = legacy_siblings(deck)
        if old:
            print(
                f"note: hand-exported companions next to {as_rel(deck, root)}. Nothing keeps\n"
                "these in sync with the deck; review and `git rm` them once the generated\n"
                "derivatives are committed:",
                file=sys.stderr,
            )
            for path in old:
                print(f"  {as_rel(path, root)}", file=sys.stderr)

    if args.check:
        problems = check_worktree(root, decks)
        if problems:
            print("stale slide-deck derivatives (agents-config Trigger Rule 40):", file=sys.stderr)
            for line in problems:
                print(line, file=sys.stderr)
            print(f"\n{FIX_HINT}", file=sys.stderr)
            return 1
        print(f"all {len(decks)} slide deck(s) in sync")
        return 0

    soffice = None if args.md_only else find_soffice()
    if not args.md_only and soffice is None and sys.platform != "darwin":
        print(
            "error: no PDF renderer. Install LibreOffice (`brew install --cask libreoffice`\n"
            "or your distro's `libreoffice`), or pass --md-only.",
            file=sys.stderr,
        )
        return 2

    manifest = load_manifest(root)
    entries = manifest.setdefault("decks", {})
    failures = 0
    synced = 0

    for deck in decks:
        rel = as_rel(deck, root)
        digest = sha256_of(deck)
        wanted = expected_derivatives(deck)
        entry = entries.setdefault(rel, {})
        recorded = entry.setdefault("derivatives", {})

        if entry.get("source_sha256") != digest:
            # The deck moved on: every recorded derivative is now stale by definition.
            recorded.clear()
        entry["source_sha256"] = digest

        did_work = False
        for kind, path in wanted.items():
            if kind == "md" and args.pdf_only:
                continue
            if kind == "pdf" and args.md_only:
                continue
            drel = as_rel(path, root)
            info = recorded.get(drel)
            fresh = (
                info is not None
                and path.exists()
                and sha256_of(path) == info.get("sha256")
            )
            if fresh and not args.force:
                continue
            try:
                if kind == "md":
                    path.write_text(pptx_to_markdown(deck, digest), encoding="utf-8")
                    detail = ""
                else:
                    engine = render_pdf(deck, path, soffice)
                    detail = f" [{engine}]"
            except DeckError as exc:
                # Leave the previous manifest entry alone. A stale-but-recorded PDF next
                # to a bumped source hash keeps --check failing, which is correct.
                print(f"error: {rel}: {kind}: {exc}", file=sys.stderr)
                recorded.pop(drel, None)
                failures += 1
                continue
            # Record only after the derivative is on disk and readable.
            written = {"kind": kind, "sha256": sha256_of(path), "bytes": path.stat().st_size}
            if kind == "pdf":
                written["renderer"] = engine
            recorded[drel] = written
            size = path.stat().st_size
            print(f"wrote {kind} ({size / 1e6:.1f} MB){detail}: {drel}")
            did_work = True

        if did_work:
            synced += 1
        elif not failures:
            print(f"up to date: {rel}")

    save_manifest(root, manifest)
    print(f"\nsynced {synced} of {len(decks)} deck(s); manifest: {MANIFEST_NAME}")
    if failures:
        print(f"{failures} derivative(s) failed — the check gate will stay red", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
