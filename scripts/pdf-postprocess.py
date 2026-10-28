"""Prepares an edition's print.html for printing to PDF.

Usage: pdf-postprocess.py <print.html> <the edition's src dir> [--romaji-toc]

The Japanese has to be tagged so it gets a Japanese font: in the Chinese edition
(lang="zh-CN") it would otherwise be drawn with Chinese glyphs (see the 置 check
in Before-you-begin). The English edition carries the same Japanese verbatim, so
every run of kana/kanji in the English source is a known Japanese string, and
occurrences of those are wrapped in <span lang="ja">. YouTube embeds can't play
on paper, so they become links. Each chapter gets its SUMMARY.md title (with the
lesson number) as a running header and as its entry in the PDF's table of
contents. With --romaji-toc the entry is the English SUMMARY.md title with the
Japanese in romaji instead, since the reMarkable draws CJK there as tofu.
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
HAS_KANJI = re.compile(f"[{KANJI}]")
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

KANA_ROMAJI = dict(zip(
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉ",
    "a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho "
    "ma mi mu me mo ya yu yo ra ri ru re ro wa o n ga gi gu ge go za ji zu ze zo da ji zu de do "
    "ba bi bu be bo pa pi pu pe po a i u e o".split(),
))
SMALL_Y = {"ゃ": "a", "ゅ": "u", "ょ": "o"}
PARTICLES = {"は": "wa", "へ": "e", "を": "o"}
# Kanji can't be romanised mechanically, so chapter titles' kanji need a reading here.
TITLE_READINGS = {
    "と思う": "to omou", "と考える": "to kangaeru", "の方が": "no hou ga", "自分": "jibun",
    "事": "koto", "物": "mono", "後": "ato", "前": "mae", "先": "saki", "時": "toki",
}


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


def kana_romaji(kana):
    kana = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in kana)
    out, double = [], False
    for c in kana:
        if c == "っ":
            double = True
            continue
        if c in SMALL_Y and out and len(out[-1]) > 1:
            stem = out[-1][:-1]
            out[-1] = stem + ("" if stem in ("sh", "ch", "j") else "y") + SMALL_Y[c]
            continue
        r = out[-1][-1] if c == "ー" and out else KANA_ROMAJI.get(c, c)
        if double:
            r = ("t" if r.startswith("ch") else r[0]) + r
            double = False
        out.append(r)
    return "".join(out)


def romaji(title):
    """The title with its Japanese in romaji."""
    def replace(m):
        run = m.group().replace("〜", "~")
        if run in TITLE_READINGS:
            return TITLE_READINGS[run]
        if HAS_KANJI.search(run):
            print(f"No romaji for {run!r} in {title!r}; add it to TITLE_READINGS", file=sys.stderr)
            return run
        # A lone or trailing は/へ/を in a title is a particle (では, ては).
        if run[-1] in PARTICLES:
            head = kana_romaji(run[:-1])
            return f"{head} {PARTICLES[run[-1]]}" if head else PARTICLES[run[-1]]
        return kana_romaji(run)
    return JAPANESE_RUN.sub(replace, title)


def summary(src):
    """(nesting level, title) of each chapter in SUMMARY.md.

    That's the order print.html lays the chapters out in; draft chapters have no
    link and are left out of both.
    """
    text = (src / "SUMMARY.md").read_text()
    return [(len(indent) // 2 + 1, title) for indent, title in SUMMARY_ENTRY.findall(text)]


def chapter_pages(html, src, romaji_toc):
    """Gives each chapter a running header and a table of contents entry."""
    chapters = HEADING.sub(r'<\1 role="none"', html).split(CHAPTER_BREAK)
    titles = toc = summary(src)
    if romaji_toc:
        toc = [(level, romaji(title)) for level, title in summary(pathlib.Path("src"))]
    if not len(chapters) == len(titles) == len(toc):
        sys.exit(f"print.html has {len(chapters)} chapters but SUMMARY.md lists {len(titles)}")

    rules = []
    for i, (chapter, (_, title), (level, toc_title)) in enumerate(zip(chapters, titles, toc)):
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
    romaji_toc = sys.argv[3:] == ["--romaji-toc"]
    html = path.read_text()
    head, rest = html.split("<main>", 1)
    main_html, tail = rest.split("</main>", 1)

    main_html = YOUTUBE.sub(r'<p><a href="https://youtu.be/\1">YouTube: youtu.be/\1</a></p>', main_html)
    main_html = tag_japanese(main_html, japanese_strings(pathlib.Path("src")))
    main_html, page_rules = chapter_pages(main_html, src, romaji_toc)
    head = head.replace("</head>", f"<style>\n{page_rules}\n</style>\n</head>")
    path.write_text(f"{head}<main>{main_html}</main>{tail}")


if __name__ == "__main__":
    main()
