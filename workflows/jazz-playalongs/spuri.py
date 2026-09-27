"""Compute Spotify-style local URIs (artist:album:title:duration) for audio files using mutagen."""
import os, sys, json, math, urllib.parse
import mutagen

def first(v):
    if v is None: return ""
    if isinstance(v, list): v = v[0] if v else ""
    return str(v)

def tags(path):
    f = mutagen.File(path)
    if f is None: return None
    t = f.tags or {}
    def g(*keys):
        for k in keys:
            try:
                if k in t:
                    val = t[k]
                    val = getattr(val, "text", val)
                    return first(val)
            except Exception: pass
        return ""
    artist = g("TPE1", "\xa9ART", "ARTIST", "artist")
    album = g("TALB", "\xa9alb", "ALBUM", "album")
    title = g("TIT2", "\xa9nam", "TITLE", "title")
    length = f.info.length if f.info else 0
    return artist, album, title, length

def uri(artist, album, title, secs):
    q = lambda s: urllib.parse.quote_plus(s, safe="")
    return f"spotify:local:{q(artist)}:{q(album)}:{q(title)}:{secs}"

if __name__ == "__main__":
    out = []
    for root in sys.argv[1:]:
        for dp, dn, fn in os.walk(root):
            for n in fn:
                if not n.lower().endswith((".mp3", ".m4a", ".mp4", ".aac", ".wav", ".aif", ".aiff", ".flac", ".ogg")): continue
                p = os.path.join(dp, n)
                try: r = tags(p)
                except Exception as e: r = None
                if not r: continue
                a, al, t, L = r
                stem = os.path.splitext(n)[0]
                out.append(dict(path=p, artist=a, album=al, title=t or stem, title_tag=t, length=L,
                                uri_floor=uri(a, al, t or stem, math.floor(L)), uri_round=uri(a, al, t or stem, round(L))))
    json.dump(out, open("local_files_uris.json", "w"), indent=1)
    print(len(out), "local audio files scanned")
