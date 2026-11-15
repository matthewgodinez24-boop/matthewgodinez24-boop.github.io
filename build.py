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
from urllib.parse import urlsplit

ROOT = Path(__file__).parent
DRAFTS = ROOT / "drafts"  # local only, listed in .gitignore
FACTS = json.loads((ROOT / "facts.json").read_text())
NAV = [("release", "ReLease"), ("reqest", "Reqest"), ("about", "About")]
MAX_WORDS = 400
SITE = "https://matthewgodinez24-boop.github.io/"  # used in link-preview tags
TOKEN = re.compile(r"\{\{(\w+)(:date)?\}\}")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
problems = []
BANNED_FILE = DRAFTS / "do-not-say.txt"  # private list, so the public repo never shows it
BANNED = (
    [p.strip() for p in BANNED_FILE.read_text().splitlines() if p.strip() and not p.startswith("#")]
    if BANNED_FILE.exists()
    else []
)


def fill(text, where):
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

    return TOKEN.sub(fact, text)


def inline(text, where):
    text = fill(text, where)
    parts, start = [], 0
    for match in LINK.finditer(text):
        parts.append(html.escape(text[start:match.start()]))
        parts.append(f'<a href="{safe_url(match.group(2), where)}">{html.escape(match.group(1))}</a>')
        start = match.end()
    parts.append(html.escape(text[start:]))
    return ''.join(parts)


def safe_url(value, where, local=False):
    parsed = urlsplit(value)
    if parsed.scheme not in ('', 'https', 'mailto') or parsed.netloc and not parsed.scheme:
        problems.append(f'{where}: unsupported URL {value}')
        return '#'
    if local and (parsed.scheme or parsed.netloc or not value.startswith('assets/')):
        problems.append(f'{where}: figures must use a local assets/ file')
        return '#'
    return html.escape(value, quote=True)


def exhibit(kind, data, where):
    if kind == 'links':
        return '<div class="actions">' + ''.join(
            f'<a href="{safe_url(fill(a["url"], where), where)}">{inline(a["label"], where)}</a>' for a in data
        ) + '</div>'
    caption = inline(data['caption'], where)
    title = f'<figcaption>{caption}</figcaption>'
    if kind == 'quote':
        return f'<figure class="excerpt"><blockquote><p>{inline(data["text"], where)}</p></blockquote>{title}</figure>'
    if kind == 'image':
        src = safe_url(data['src'], where, local=True)
        if not (ROOT / data['src']).is_file():
            problems.append(f'{where}: missing image {data["src"]}')
        alt = html.escape(fill(data['alt'], where), quote=True)
        if not alt.strip() or data['width'] <= 0 or data['height'] <= 0:
            problems.append(f'{where}: figure requires alt text and positive dimensions')
        return (f'<figure class="screenshot"><a href="{src}" aria-label="Open full-size image: {alt}">'
                f'<img src="{src}" alt="{alt}" width="{int(data["width"])}" height="{int(data["height"])}" '
                f'loading="lazy" decoding="async"></a>{title}</figure>')
    if kind == 'table':
        header = ''.join(f'<th scope="col">{inline(c, where)}</th>' for c in data['headers'])
        rows = ''.join('<tr>' + ''.join(f'<td>{inline(c, where)}</td>' for c in row) + '</tr>' for row in data['rows'])
        return f'<figure class="data"><table><caption>{caption}</caption><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></figure>'
    raise ValueError(f'{where}: unknown exhibit @{kind}')


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
        if s.startswith('@'):
            close()
            kind, _, payload = s[1:].partition(' ')
            out.append(exhibit(kind, json.loads(payload), where))
        elif numbered or s.startswith("- "):
            tag = "ol" if numbered else "ul"
            if open_list != tag:
                close()
                out.append(f"<{tag}>")
                open_list = tag
            out.append(f"<li>{inline(numbered.group(1) if numbered else s[2:], where)}</li>")
        elif s.startswith("## "):
            close()
            heading = s[3:]
            anchor = re.search(r' \{#([a-z][a-z0-9-]*)\}$', heading)
            section_id = f' id="{anchor[1]}"' if anchor else ''
            if anchor:
                heading = heading[:anchor.start()]
            out.append(("</section>" if in_section else "") + f"<section{section_id}><h2>{inline(heading, where)}</h2>")
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
    # Exhibit dimensions and asset filenames are implementation data, not claims.
    prose = re.sub(r'(?m)^@.*$', '', head + body)
    for line in body.splitlines():
        if line.startswith('@'):
            kind, _, payload = line[1:].partition(' ')
            data = json.loads(payload)
            if kind == 'links':
                prose += '\n' + ' '.join(a['label'] for a in data)
            else:
                prose += '\n' + data['caption']
                prose += '\n' + data.get('text', '') + data.get('alt', '')
                if kind == 'table':
                    prose += '\n' + ' '.join(data['headers']) + ' '.join(c for row in data['rows'] for c in row)
    words_only = re.sub(r"(?m)^\d+\. ", "", LINK.sub(r"\1", TOKEN.sub("", prose)))
    for loose in re.findall(r"\S*\d\S*", words_only):
        problems.append(f"{where}: '{loose}' is typed in the text. Move the number to facts.json")

    main = render(body, where)
    text = html.unescape(re.sub(r"<[^>]+>", " ", main))
    count = len(text.split())
    if count > MAX_WORDS:
        problems.append(f"{where}: {count} words, the limit is {MAX_WORDS}")

    title = html.escape(fill(meta["title"] if slug == "index" else f"{meta['title']} · Mathew Godinez", where))
    description = html.escape(fill(meta.get("description", ""), where))
    url = SITE if slug == "index" else f"{SITE}{slug}.html"
    nav = "\n".join(
        f'<a href="{up}{s}.html"{" aria-current=page" if s == slug else ""}>{label}</a>' for s, label in NAV
    )
    banner = '<p class="draft">Draft. Not published. This file stays on this computer.</p>\n' if draft else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}assets/social-preview.png">
<meta property="og:image:alt" content="Mathew Godinez. Growth and go-to-market. ReLease, outreach workflows, and Reqest.">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}style.css">
</head>
<body class="{slug}">
<a class="skip" href="#main">Skip to content</a>
<header>
<a class="name" href="{up}index.html">Mathew Godinez</a>
<nav aria-label="Pages">
{nav}
</nav>
</header>
<main id="main">
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


if __name__ == '__main__':
    for name, entry in FACTS.items():
        if name.startswith('_'):
            continue
        if not entry.get('ledger') or not entry.get('measured'):
            problems.append(f'facts.json: {name} needs a ledger source and evidence date')
    for src in sorted((ROOT / "content").glob("*.txt")):
        print(f"built {src.stem:<10} {build(src, ROOT, draft=False)} words")
    for src in sorted((DRAFTS / "content").glob("*.txt")):
        print(f"built draft {src.stem} ({build(src, DRAFTS, draft=True)} words, local only)")
    check_do_not_say((ROOT / "facts.json").read_text(), "facts.json")
    if not BANNED:
        print("Note: drafts/do-not-say.txt is missing, so the do-not-say check was skipped.")
    if problems:
        print(f"\n{len(problems)} problem(s). Do not publish yet:")
        print("\n".join(f"  - {p}" for p in problems))
        sys.exit(1)
    print("\nAll checks passed.")
