import re
from pathlib import Path


PAGE_PATTERN = re.compile(r"\(ص:\s*(\d+)\)")


def load_txt(txt_path: str):
    path = Path(txt_path)

    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    pages = []
    current_page = None
    current_lines = []

    for line in lines:
        match = PAGE_PATTERN.search(line)

        if match:
            if current_page is not None and current_lines:
                page_text = "\n".join(current_lines).strip()

                if page_text:
                    pages.append({
                        "text": page_text,
                        "page": current_page,
                        "source": str(path),
                    })

            current_page = int(match.group(1))
            current_lines = []
            continue

        if current_page is not None:
            current_lines.append(line)

    if current_page is not None and current_lines:
        page_text = "\n".join(current_lines).strip()

        if page_text:
            pages.append({
                "text": page_text,
                "page": current_page,
                "source": str(path),
            })

    return pages
