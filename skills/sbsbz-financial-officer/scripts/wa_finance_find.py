#!/usr/bin/env python3
"""Find invoices, quotes and payment messages in Brando's local WhatsApp desktop data.

Read-only: copies ChatStorage.sqlite (plus -wal/-shm) to a temporary folder and
queries the copy, so WhatsApp itself is never touched. Prints only messages that
carry a document/image or match a finance keyword, never whole conversations.

Examples:
  wa_finance_find.py --list-chats "jordan"
  wa_finance_find.py --chat "Jordan" --chat "Awesome Jordan" --since 2026-09-01
  wa_finance_find.py --chat "Awesome Jordan" --since 2026-09-20 --types document \
      --copy-to ~/sbsbz/events/MM-DD-YYYY-fo-task/private/source
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

WA = Path.home() / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared"
APPLE_EPOCH = 978307200  # seconds between 1970-01-01 and 2001-01-01
TYPES = {0: "text", 1: "image", 2: "video", 3: "audio", 7: "link", 8: "document", 15: "sticker"}
KEYWORDS = r"invoice|quote|receipt|pay|paid|venmo|zelle|reimburs|fund|grant|gsc|assu|\$\s?\d|budget|rate"


def open_copy():
    db = WA / "ChatStorage.sqlite"
    if not db.exists():
        sys.exit(f"WhatsApp database not found at {db}. Is the WhatsApp desktop app installed and signed in?")
    tmp = Path(tempfile.mkdtemp(prefix="wa-ro-"))
    for suffix in ("", "-wal", "-shm"):
        src = WA / f"ChatStorage.sqlite{suffix}"
        if src.exists():
            shutil.copy2(src, tmp / src.name)
    con = sqlite3.connect(f"file:{tmp / 'ChatStorage.sqlite'}?mode=ro", uri=True)
    return con, tmp


def ts(apple_seconds):
    return dt.datetime.fromtimestamp(apple_seconds + APPLE_EPOCH)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "chat").lower()).strip("-")[:40]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-chats", metavar="NAME", help="list chats whose name contains NAME and exit")
    ap.add_argument("--chat", action="append", default=[], help="chat-name substring (repeatable)")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD (default: 45 days ago)")
    ap.add_argument("--types", default="document,image", help="media types to list: document,image,audio,video")
    ap.add_argument("--keywords", default=KEYWORDS, help="regex for finance text messages ('' to skip text)")
    ap.add_argument("--copy-to", default=None, help="copy matching media here and write manifest.json")
    args = ap.parse_args()

    con, tmp = open_copy()
    try:
        if args.list_chats is not None:
            rows = con.execute(
                "select Z_PK, ZPARTNERNAME, ZLASTMESSAGEDATE from ZWACHATSESSION "
                "where ZPARTNERNAME like ? order by ZLASTMESSAGEDATE desc limit 40",
                (f"%{args.list_chats}%",)).fetchall()
            for pk, name, last in rows:
                print(f"{pk:>6}  {ts(last or 0):%m-%d-%Y %H:%M}  {name}")
            return
        if not args.chat:
            sys.exit("Give --chat (or --list-chats first).")
        since = dt.datetime.strptime(args.since, "%Y-%m-%d") if args.since else dt.datetime.now() - dt.timedelta(days=45)
        since_apple = since.timestamp() - APPLE_EPOCH
        sessions = {}
        for needle in args.chat:
            for pk, name in con.execute("select Z_PK, ZPARTNERNAME from ZWACHATSESSION where ZPARTNERNAME like ?",
                                        (f"%{needle}%",)):
                sessions[pk] = name
        if not sessions:
            sys.exit("No chat matched; try --list-chats.")
        want = {k for k, v in TYPES.items() if v in args.types.split(",")}
        kw = re.compile(args.keywords, re.I) if args.keywords else None
        q = ("select m.Z_PK, m.ZCHATSESSION, m.ZMESSAGEDATE, m.ZISFROMME, m.ZMESSAGETYPE, m.ZTEXT, "
             "mi.ZMEDIALOCALPATH, mi.ZTITLE, mi.ZFILESIZE from ZWAMESSAGE m "
             "left join ZWAMEDIAITEM mi on mi.Z_PK = m.ZMEDIAITEM "
             f"where m.ZCHATSESSION in ({','.join('?' * len(sessions))}) and m.ZMESSAGEDATE >= ? "
             "order by m.ZMESSAGEDATE")
        manifest = []
        dest = Path(args.copy_to).expanduser() if args.copy_to else None
        if dest:
            dest.mkdir(parents=True, exist_ok=True)
        for pk, chat, when, from_me, mtype, text, path, title, size in con.execute(q, (*sessions, since_apple)):
            is_media = mtype in want and path
            is_kw = kw and text and kw.search(text)
            if not (is_media or is_kw):
                continue
            who = "Brando" if from_me else "them"
            body = (title or text or "").replace("\n", " / ")[:200]
            line = f"{ts(when):%m-%d-%Y %H:%M} | {sessions[chat]} | {who} | {TYPES.get(mtype, mtype)} | {body}"
            if is_media:
                line += f" | {path} ({size or 0} bytes)"
            print(line)
            if dest and is_media:
                src = WA / "Message" / path
                if not src.exists():
                    print(f"   ! media not downloaded on this Mac: {src} (open the chat in WhatsApp and download it)")
                    continue
                out = dest / f"{ts(when):%m-%d-%Y}-{slug(sessions[chat])}-{pk}{src.suffix}"
                shutil.copy2(src, out)
                digest = hashlib.sha256(out.read_bytes()).hexdigest()
                manifest.append({"file": out.name, "sha256": digest, "chat": sessions[chat], "message_id": pk,
                                 "sent_local": f"{ts(when):%Y-%m-%d %H:%M:%S}", "from_me": bool(from_me),
                                 "caption": title or text, "whatsapp_path": path})
                print(f"   -> copied {out} sha256={digest[:12]}")
        if dest and manifest:
            (dest / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
            print(f"Wrote {dest / 'manifest.json'} ({len(manifest)} files)")
    finally:
        con.close()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
