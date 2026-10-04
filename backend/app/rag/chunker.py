def chunk_pages(pages, chunk_size=1000, overlap=200, min_chunk_size=120):
    chunks = []

    for page in pages:
        text = page["text"]
        page_number = page["page"]
        source = page["source"]

        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()

            if len(chunk_text) >= min_chunk_size:
                chunks.append({
                    "text": chunk_text,
                    "page": page_number,
                    "source": source,
                })

            start += chunk_size - overlap

    return chunks
