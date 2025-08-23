#!/usr/bin/env python3
"""
extract_exercises.py

Extract end-of-chapter exercises/problems for each chapter into separate PDFs.

Strategy:
  1) Use TOC/bookmarks (level 1) to find chapter start pages.
  2) If no usable TOC, scan pages for headings like "Chapter N" or "N Title".
  3) For each chapter, find the exercises start page by:
       a) Looking for top-of-page headings: "Exercises", "Problems", etc.
       b) If none found, detect dense numbering like "N.x" (e.g., "12.3", "12.10").
  4) Export range [exercises_start, chapter_end] to "<stem>_Chapter-XX_Exercises.pdf".

Install:
  pip install pymupdf

Usage:
  python extract_exercises.py "Book.pdf"
  # Optional: customize keywords / thresholds
  python extract_exercises.py "Book.pdf" --min-num-count 2 --keywords Exercises Problems "Review Questions"

Notes:
  - For scanned PDFs with no text, run OCR first (e.g., with ocrmypdf), then use this script.
"""

import argparse
import pathlib
import re
import sys
from typing import List, Tuple, Optional

import fitz  # PyMuPDF


# ---------- Configurable defaults ----------
DEFAULT_KEYWORDS = [
    "Exercises",
    "PROBLEMS",
    "Problems",
    "Review Exercises",
    "Review Questions",
    "Exercises and Problems",
]
CHAPTER_HEADING_PATTERNS = [
    re.compile(r'^\s*Chapter\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'^\s*CHAPTER\s+(\d+)\b'),
    # Numeric first-level style, e.g. "1 Probability Theory"
    re.compile(r'^\s*(\d+)\s+[A-Z][A-Za-z].*'),
]
# ------------------------------------------


def slugify(s: str) -> str:
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')
    return s[:60] or "Exercises"


def get_toc_chapter_starts(doc: fitz.Document) -> List[Tuple[int, int, str]]:
    """
    Return chapter starts from TOC:
      [(chapter_number, start_page_index, title), ...] sorted by start page.

    If title doesn't contain a number, assign chapter_number by order.
    """
    toc = doc.get_toc(simple=True)  # [ [level, title, page1based], ... ]
    if not toc:
        return []

    chapters = []
    seen_nums = set()
    for level, title, p1 in toc:
        if level != 1:
            continue
        ch_num = None
        for rx in CHAPTER_HEADING_PATTERNS:
            m = rx.match(title.strip())
            if m:
                try:
                    ch_num = int(m.group(1))
                except Exception:
                    ch_num = None
                break
        if ch_num is None:
            ch_num = len(chapters) + 1  # fallback numbering by order

        if ch_num in seen_nums:
            # Avoid duplicates if TOC has repeated level-1 entries
            continue
        seen_nums.add(ch_num)
        chapters.append((ch_num, p1 - 1, title.strip()))

    chapters.sort(key=lambda x: x[1])
    return chapters


def scan_for_chapter_starts(doc: fitz.Document) -> List[Tuple[int, int, str]]:
    """
    Fallback when no TOC: scan pages for "Chapter N" or "N Title" patterns near the top.
    Return [(chapter_number, start_page_index, title_or_line), ...] ordered by chapter number.
    """
    starts = {}
    for i in range(doc.page_count):
        text = doc.load_page(i).get_text("text") or ""
        lines = [ln.strip() for ln in text.splitlines()[:25]]
        for ln in lines:
            for rx in CHAPTER_HEADING_PATTERNS:
                m = rx.match(ln)
                if m:
                    try:
                        ch = int(m.group(1))
                        if ch not in starts:
                            starts[ch] = (ch, i, ln)
                        break
                    except Exception:
                        pass
            else:
                continue
            break
    if not starts:
        return []
    return sorted(starts.values(), key=lambda x: (x[0], x[1]))


def build_chapter_ranges(starts: List[Tuple[int, int, str]], total_pages: int) -> List[Tuple[int, int, int, str]]:
    """
    Given chapter starts [(ch_num, start_idx, title)], build ranges
    [(ch_num, start_idx, end_idx, title)].
    """
    ranges = []
    if not starts:
        return ranges
    starts_sorted = sorted(starts, key=lambda x: x[1])  # by page
    for idx, (ch, sp, title) in enumerate(starts_sorted):
        ep = (starts_sorted[idx + 1][1] - 1) if idx + 1 < len(starts_sorted) else (total_pages - 1)
        if ep >= sp:
            ranges.append((ch, sp, ep, title))
    return ranges


def page_has_heading(text: str, keywords: List[str], top_lines: int = 25) -> bool:
    """
    Check if page has a heading line that starts with any keyword, looking only in the top few lines.
    """
    lines = [ln.strip() for ln in text.splitlines()[:top_lines]]
    for ln in lines:
        for kw in keywords:
            # exact prefix match (case sensitive for style preservation, but compare case-insensitively)
            if ln.lower().startswith(kw.lower()):
                return True
    return False


def detect_exercises_start(
    doc: fitz.Document,
    ch_range: Tuple[int, int, int, str],
    keywords: List[str],
    min_num_count: int = 2,
) -> Optional[int]:
    """
    Detect the page index within [start, end] where exercises/problems begin.

    Heuristics:
      1) Look for heading keywords near top of the page.
      2) If missing, count lines that look like '<chapter>.<number>' (e.g., '12.5'):
         - Scan from the end toward the front (exercises usually near the end).
         - Pick the earliest-from-end page that has >= min_num_count such lines.
    """
    ch_num, start, end, _title = ch_range

    # 1) Heading-based detection (scan start->end)
    for i in range(start, end + 1):
        text = doc.load_page(i).get_text("text") or ""
        if page_has_heading(text, keywords):
            return i

    # 2) Numbering density detection (scan end->start)
    rx_num = re.compile(rf'^\s*{ch_num}\.\d+\b')
    for i in range(end, start - 1, -1):
        text = doc.load_page(i).get_text("text") or ""
        cnt = sum(1 for ln in text.splitlines() if rx_num.match(ln.strip()))
        if cnt >= min_num_count:
            # Walk backward to include any preceding page with a header like "Exercises 12"
            # If previous page top contains the keyword, shift start one page earlier.
            if i - 1 >= start:
                prev_text = doc.load_page(i - 1).get_text("text") or ""
                if page_has_heading(prev_text, keywords):
                    return i - 1
            return i

    return None


def extract_pdf_range(doc: fitz.Document, start: int, end: int, outfile: pathlib.Path) -> None:
    out = fitz.open()
    out.insert_pdf(doc, from_page=start, to_page=end)
    out.save(outfile.as_posix())
    out.close()


def main():
    ap = argparse.ArgumentParser(description="Extract end-of-chapter exercise/problem pages into per-chapter PDFs.")
    ap.add_argument("pdf", help="Input PDF path")
    ap.add_argument("--outdir", default=None, help="Output directory (default: <stem>_exercises)")
    ap.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS,
                    help="Headings that mark exercises (default: %(default)s)")
    ap.add_argument("--min-num-count", type=int, default=2,
                    help="Min number of '<chapter>.<n>' lines to treat a page as exercises (default: %(default)s)")
    args = ap.parse_args()

    inpath = pathlib.Path(args.pdf)
    if not inpath.exists():
        print(f"[ERROR] File not found: {inpath}", file=sys.stderr)
        sys.exit(1)

    try:
        doc = fitz.open(inpath.as_posix())
    except Exception as e:
        print(f"[ERROR] Could not open PDF: {e}", file=sys.stderr)
        sys.exit(1)

    # Prefer TOC; fallback to scanning
    starts = get_toc_chapter_starts(doc)
    if len(starts) < 2:
        print("[INFO] TOC not found or too small; scanning for chapter starts…")
        starts = scan_for_chapter_starts(doc)

    if not starts:
        print("[ERROR] Could not detect chapter starts (no TOC and no 'Chapter N' headings).", file=sys.stderr)
        print("       Tip: OCR your PDF first if it's scanned, then try again.", file=sys.stderr)
        sys.exit(2)

    ranges = build_chapter_ranges(starts, doc.page_count)
    if not ranges:
        print("[ERROR] Could not build chapter ranges.", file=sys.stderr)
        sys.exit(3)

    outdir = pathlib.Path(args.outdir) if args.outdir else inpath.with_suffix("").parent / (inpath.stem + "_exercises")
    outdir.mkdir(parents=True, exist_ok=True)

    made_any = False
    for ch_num, sp, ep, title in ranges:
        ex_start = detect_exercises_start(doc, (ch_num, sp, ep, title), keywords=args.keywords, min_num_count=args.min_num_count)
        if ex_start is None:
            print(f"[WARN] Chapter {ch_num:02d}: no exercises/probs detected (pages {sp+1}-{ep+1}, title: {title!r}).")
            continue

        # Save [ex_start..ep]
        safe_title = slugify(title)
        outfile = outdir / f"{inpath.stem}_Chapter-{ch_num:02d}_{safe_title}_Exercises.pdf"
        extract_pdf_range(doc, ex_start, ep, outfile)
        made_any = True
        print(f"[OK] Wrote: {outfile.name}  (Chapter {ch_num:02d}, pages {ex_start+1}-{ep+1})")

    doc.close()
    if not made_any:
        print("[INFO] No exercise sections were found. Try adjusting --keywords or --min-num-count.", file=sys.stderr)


if __name__ == "__main__":
    main()
