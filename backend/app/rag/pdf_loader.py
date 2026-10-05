import pymupdf


def load_pdf(pdf_path: str):
    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text").strip()

        if text:
            pages.append({
                "text": text,
                "page": page_number,
                "source": pdf_path,
            })

    document.close()

    return pages

