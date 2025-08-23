import re
import sys
import pathlib
import fitz  # PyMuPDF

CHAPTER_PATTERNS = [
    re.compile(r'^\s*Chapter\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'^\s*CHAPTER\s+(\d+)\b'),
    re.compile(r'^\s*(\d+)\s+[A-Z][A-Za-z].*'),  # e.g., "1 Probability Theory"
]

def slugify(s: str) -> str:
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')
    return s[:60] or "Chapter"

def detect_chapters_by_toc(doc):
    """Return list of (chapter_num, start_page_index, title) from TOC if present."""
    toc = doc.get_toc(simple=True)  # [ [level, title, page1based], ... ]
    chapters = []
    seen = set()
    for level, title, p1 in toc:
        if level != 1:
            continue
        # try to parse chapter number from title; if not, assign by order
        chnum = None
        for rx in CHAPTER_PATTERNS:
            m = rx.match(title.strip())
            if m:
                try:
                    chnum = int(m.group(1))
                except Exception:
                    pass
                break
        if chnum is None:
            chnum = len(chapters) + 1
        if chnum in seen:
            continue
        seen.add(chnum)
        chapters.append((chnum, p1 - 1, title.strip()))
    chapters.sort(key=lambda x: x[1])
    return chapters

def detect_chapters_by_scanning(doc):
    """Fallback: scan pages for lines like 'Chapter N' near the top."""
    chapters = {}
    for i in range(doc.page_count):
        text = (doc.load_page(i).get_text("text") or "")
        lines = [ln.strip() for ln in text.splitlines()[:20]]  # top portion
        for ln in lines:
            for rx in CHAPTER_PATTERNS:
                m = rx.match(ln)
                if m:
                    try:
                        ch = int(m.group(1))
                        if ch not in chapters:
                            chapters[ch] = (ch, i, ln)
                        break
                    except Exception:
                        pass
            else:
                continue
            break
    # Return sorted by chapter number, then by page
    return sorted(chapters.values(), key=lambda x: (x[0], x[1]))

def build_ranges(starts, total_pages):
    """Given [(chnum, start_idx, title)], return [(chnum, start_idx, end_idx, title)]."""
    ranges = []
    for idx, (chn, sp, title) in enumerate(starts):
        ep = (starts[idx + 1][1] - 1) if idx + 1 < len(starts) else (total_pages - 1)
        if ep >= sp:
            ranges.append((chn, sp, ep, title))
    return ranges

def main(inpdf):
    inpath = pathlib.Path(inpdf)
    if not inpath.exists():
        sys.exit(f"File not found: {inpdf}")

    doc = fitz.open(inpdf)

    # 1) Prefer TOC / bookmarks
    starts = detect_chapters_by_toc(doc)

    # 2) Fallback to text scanning if TOC absent or too few hits
    if len(starts) < 2:
        starts = detect_chapters_by_scanning(doc)

    if not starts:
        sys.exit("Could not auto-detect chapter starts (no TOC and no 'Chapter N' headings found).")

    ranges = build_ranges(starts, doc.page_count)

    outdir = inpath.with_suffix("").as_posix() + "_chapters"
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)

    for chn, sp, ep, title in ranges:
        # Generate a neat filename with title if possible
        safe_title = slugify(title)
        outfile = pathlib.Path(outdir) / f"{inpath.stem}_Chapter-{chn:02d}_{safe_title}.pdf"

        # Write this range using PyMuPDF (fast and keeps fidelity)
        outdoc = fitz.open()
        outdoc.insert_pdf(doc, from_page=sp, to_page=ep)
        outdoc.save(outfile.as_posix())
        outdoc.close()
        print(f"Wrote: {outfile}")

    doc.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_pdf_chapters.py input.pdf")
        sys.exit(1)
    main(sys.argv[1])
