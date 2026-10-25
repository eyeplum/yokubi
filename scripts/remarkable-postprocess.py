"""Prepares an edition's print.html for printing to the reMarkable PDF.

Usage: remarkable-postprocess.py <print.html> <the edition's src dir>

The Japanese has to be tagged so it gets a Japanese font: in the Chinese edition
(lang="zh-CN") it would otherwise be drawn with Chinese glyphs (see the 置 check
in Before-you-begin). The English edition carries the same Japanese verbatim, so
every run of kana/kanji in the English source is a known Japanese string, and
occurrences of those are wrapped in <span lang="ja">. YouTube embeds can't play
on paper, so they become links. Each chapter gets its SUMMARY.md title (with the
lesson number) as a running header, and its English SUMMARY.md title as its entry
in the PDF's table of contents, since the reMarkable draws Chinese there as tofu.
"""
import pathlib
import re
import sys
from html import escape

FURIGANA = re.compile(r"\{f\|([^{}|\n]+)\|([^{}|\n]+)\}")
KANA = "぀-ゟ゠-ヿー"
KANJI = "㐀-䶿一-鿿豈-﫿々〆"
JAPANESE_RUN = re.compile(f"[{KANA}{KANJI}〜]+")
HAS_KANA = re.compile(f"[{KANA}]")
CJK = re.compile(f"[{KANA}{KANJI}]")
STANDALONE_KANJI = re.compile(f"(?<![{KANA}{KANJI}])[{KANJI}]+(?![{KANA}{KANJI}])")
# Ranges separated only by these are merged into one span.
JAPANESE_GAP = re.compile(r"[\s、。「」『』？！・…　]*")

TAG = re.compile(r"(<[^>]+>)")
INLINE_TAGS = {"a", "b", "code", "em", "i", "ruby", "span", "strong"}
YOUTUBE = re.compile(r'<iframe[^>]*src="https://www\.youtube\.com/embed/([\w-]+)[^"]*"[^>]*></iframe>')
CHAPTER_BREAK = '<div style="break-before: page; page-break-before: always;"></div>'
SUMMARY_ENTRY = re.compile(r"^( *)(?:- )?\[([^\]]+)\]\([^)]+\)", re.M)
HEADING = re.compile(r"<(h[1-6])\b")


def japanese_strings(src):
    strings = set()
    for path in src.rglob("*.md"):
        text = TAG.sub("", FURIGANA.sub(r"\1", path.read_text()))
        strings.update(JAPANESE_RUN.findall(text))
    return sorted(strings, key=len, reverse=True)


def fits_charset(s, encoding):
    try:
        s.encode(encoding)
        return True
    except UnicodeEncodeError:
        return False


def is_chinese_charset(s):
    return fits_charset(s, "gb2312")


def japanese_ranges(text, strings):
    """Character ranges of `text` that are Japanese."""
    found = []
    for m in re.finditer("|".join(map(re.escape, strings)), text):
        word = m.group()
        # A kanji-only string like 自然 may just be Chinese. Trust it only if it
        # uses a character simplified Chinese doesn't, or stands on its own.
        if not HAS_KANA.search(word) and is_chinese_charset(word):
            before = text[m.start() - 1:m.start()]
            after = text[m.end():m.end() + 1]
            if CJK.match(before) or CJK.match(after):
                continue
        found.append((m.start(), m.end()))
    # Terms only the translation uses, like （助数詞）.
    for m in STANDALONE_KANJI.finditer(text):
        if fits_charset(m.group(), "cp932") and not is_chinese_charset(m.group()):
            found.append((m.start(), m.end()))

    ranges = []
    for start, end in sorted(set(found)):
        if ranges and start <= ranges[-1][1]:
            ranges[-1][1] = max(ranges[-1][1], end)
        elif ranges and JAPANESE_GAP.fullmatch(text, ranges[-1][1], start):
            ranges[-1][1] = end
        else:
            ranges.append([start, end])
    return ranges


def tag_japanese(html, strings):
    tokens = TAG.split(html)
    # Join the text of each block (inline tags are transparent) so a word split
    # by <b> or <ruby> still matches. Readings in <rt> are left out.
    text, offsets, in_rt = [], {}, False
    pos = 0
    for i, token in enumerate(tokens):
        if i % 2 == 0:
            if not in_rt:
                offsets[i] = pos
                text.append(token)
                pos += len(token)
            continue
        name = re.match(r"</?(\w+)", token)
        name = name.group(1).lower() if name else ""
        if name == "rt":
            in_rt = not token.startswith("</")
        elif name not in INLINE_TAGS:
            text.append("\n")
            pos += 1
    ranges = japanese_ranges("".join(text), strings)

    r = 0
    for i, start in offsets.items():
        token, end = tokens[i], start + len(tokens[i])
        pieces, cursor = [], start
        while r < len(ranges) and ranges[r][0] < end:
            lo, hi = max(ranges[r][0], start), min(ranges[r][1], end)
            if token[lo - start:hi - start].strip():
                pieces.append(token[cursor - start:lo - start])
                pieces.append(f'<span lang="ja">{token[lo - start:hi - start]}</span>')
                cursor = hi
            if ranges[r][1] > end:
                break
            r += 1
        pieces.append(token[cursor - start:])
        tokens[i] = "".join(pieces)
    return "".join(tokens).replace("<ruby>", '<ruby lang="ja">')


def summary(src):
    """(nesting level, title) of each chapter in SUMMARY.md.

    That's the order print.html lays the chapters out in; draft chapters have no
    link and are left out of both.
    """
    text = (src / "SUMMARY.md").read_text()
    return [(len(indent) // 2 + 1, title) for indent, title in SUMMARY_ENTRY.findall(text)]


def chapter_pages(html, src):
    """Gives each chapter a running header and an English table of contents entry."""
    chapters = HEADING.sub(r'<\1 role="none"', html).split(CHAPTER_BREAK)
    titles, english = summary(src), summary(pathlib.Path("src"))
    if not len(chapters) == len(titles) == len(english):
        sys.exit(f"print.html has {len(chapters)} chapters but SUMMARY.md lists {len(titles)}")

    rules = []
    for i, (chapter, (_, title), (level, toc_title)) in enumerate(zip(chapters, titles, english)):
        # Chrome builds the PDF's outline from the headings it paints and doesn't
        # take role="none" ones, so this invisible heading is the chapter's entry.
        chapter = f'<h{level} class="toc-entry">{escape(toc_title)}</h{level}>{chapter}'
        # The front page goes without a header.
        if not i:
            chapters[i] = chapter
            continue
        title = title.replace("\\", "\\\\").replace('"', '\\"')
        rules.append(f'@page chapter-{i} {{ @top-center {{ content: "{title}"; }} }}')
        # Keep the break inside the named page; on its own it'd get a blank page.
        chapters[i] = f'<div style="page: chapter-{i}">{CHAPTER_BREAK}{chapter}</div>'
    return "".join(chapters), "\n".join(rules)


def main():
    path, src = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    html = path.read_text()
    head, rest = html.split("<main>", 1)
    main_html, tail = rest.split("</main>", 1)

    main_html = YOUTUBE.sub(r'<p><a href="https://youtu.be/\1">YouTube: youtu.be/\1</a></p>', main_html)
    main_html = tag_japanese(main_html, japanese_strings(pathlib.Path("src")))
    main_html, page_rules = chapter_pages(main_html, src)
    head = head.replace("</head>", f"<style>\n{page_rules}\n</style>\n</head>")
    path.write_text(f"{head}<main>{main_html}</main>{tail}")


if __name__ == "__main__":
    main()
