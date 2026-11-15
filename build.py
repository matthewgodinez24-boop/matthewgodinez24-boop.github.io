#!/usr/bin/env python3
"""Builds the site: content/*.txt (words) + facts.json (numbers) -> *.html.

Run:  python3 build.py
It always writes the pages, then exits 1 and lists the problems if a public
page breaks a rule. Do not commit or push until it exits 0.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DRAFTS = ROOT / "drafts"  # local only, listed in .gitignore
FACTS = json.loads((ROOT / "facts.json").read_text())
NAV = [("release", "ReLease"), ("reqest", "Reqest"), ("about", "About")]
MAX_WORDS = 400
TOKEN = re.compile(r"\{\{(\w+)(:date)?\}\}")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
problems = []
BANNED_FILE = DRAFTS / "do-not-say.txt"  # private list, so the public repo never shows it
BANNED = (
    [p.strip() for p in BANNED_FILE.read_text().splitlines() if p.strip() and not p.startswith("#")]
    if BANNED_FILE.exists()
    else []
)


def inline(text, where):
    def fact(m):
        entry = FACTS.get(m.group(1))
        if not isinstance(entry, dict):
            problems.append(f"{where}: {m.group(0)} is not in facts.json")
            return m.group(0)
        if not m.group(2):
            return entry["value"]
        if not entry.get("measured"):
            problems.append(f"{where}: {m.group(0)} has no ledger date in facts.json")
            return m.group(0)
        return date.fromisoformat(entry["measured"]).strftime("%b %-d, %Y")

    return LINK.sub(r'<a href="\2">\1</a>', html.escape(TOKEN.sub(fact, text), quote=False))


def render(body, where):
    out, para, open_list, in_section = [], [], None, False

    def close():
        nonlocal open_list
        if para:
            out.append(f"<p>{inline(' '.join(para), where)}</p>")
            para.clear()
        if open_list:
            out.append(f"</{open_list}>")
            open_list = None

    for line in body.splitlines():
        s = line.strip()
        numbered = re.match(r"\d+\. (.*)", s)
        if numbered or s.startswith("- "):
            tag = "ol" if numbered else "ul"
            if open_list != tag:
                close()
                out.append(f"<{tag}>")
                open_list = tag
            out.append(f"<li>{inline(numbered.group(1) if numbered else s[2:], where)}</li>")
        elif s.startswith("## "):
            close()
            out.append(("</section>" if in_section else "") + f"<section><h2>{inline(s[3:], where)}</h2>")
            in_section = True
        elif s.startswith("# "):
            close()
            out.append(f"<h1>{inline(s[2:], where)}</h1>")
        elif s:
            if open_list:
                close()
            para.append(s)
        else:
            close()
    close()
    return "\n".join(out) + ("\n</section>" if in_section else "")


def check_do_not_say(text, where):
    for phrase in BANNED:
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text, re.I):
            problems.append(f"{where}: contains the do-not-say phrase '{phrase}'")


def build(src, out_dir, draft):
    where = str(src.relative_to(ROOT))
    head, _, body = src.read_text().partition("\n---\n")
    meta = dict(line.split(": ", 1) for line in head.splitlines() if ": " in line)
    slug = "index" if src.stem == "home" else src.stem
    up = "../" if draft else ""

    # Numbers belong in facts.json: no digit may be typed straight into the words.
    words_only = re.sub(r"(?m)^\d+\. ", "", LINK.sub(r"\1", TOKEN.sub("", head + body)))
    for loose in re.findall(r"\S*\d\S*", words_only):
        problems.append(f"{where}: '{loose}' is typed in the text. Move the number to facts.json")

    main = render(body, where)
    text = html.unescape(re.sub(r"<[^>]+>", " ", main))
    count = len(text.split())
    if count > MAX_WORDS:
        problems.append(f"{where}: {count} words, the limit is {MAX_WORDS}")

    title = meta["title"] if slug == "index" else f"{meta['title']} · Mathew Godinez"
    nav = "\n".join(
        f'<a href="{up}{s}.html"{" aria-current=page" if s == slug else ""}>{label}</a>' for s, label in NAV
    )
    banner = '<p class="draft">Draft. Not published. This file stays on this computer.</p>\n' if draft else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(meta.get('description', ''))}">
<link rel="stylesheet" href="{up}style.css">
</head>
<body class="{slug}">
<header>
<a class="name" href="{up}index.html">Mathew Godinez</a>
<nav aria-label="Pages">
{nav}
</nav>
</header>
<main>
{banner}{main}
</main>
</body>
</html>
"""
    (out_dir / f"{slug}.html").write_text(page)

    if not draft:
        for gap in sorted(set(re.findall(r"\[NEEDS [^\]]*\]", text))):
            problems.append(f"{where}: still contains {gap}")
        check_do_not_say(page, where)
    return count


for src in sorted((ROOT / "content").glob("*.txt")):
    print(f"built {src.stem:<10} {build(src, ROOT, draft=False)} words")
for src in sorted((DRAFTS / "content").glob("*.txt")):
    print(f"built draft {src.stem} ({build(src, DRAFTS, draft=True)} words, local only)")

# facts.json is public too, so it gets the same check as the pages.
check_do_not_say((ROOT / "facts.json").read_text(), "facts.json")
if not BANNED:
    print("Note: drafts/do-not-say.txt is missing, so the do-not-say check was skipped.")

if problems:
    print(f"\n{len(problems)} problem(s). Do not publish yet:")
    print("\n".join(f"  - {p}" for p in problems))
    sys.exit(1)
print("\nAll checks passed.")
