from typing import List
import re

def chunk(text: str, size: int = 750, overlap: int = 120) -> List[str]:
    """
    Split text into overlapping word chunks for embedding.
    Example: if size=750 and overlap=120, each chunk has ~750 words
    and overlaps the previous one by 120 words.
    """
    words = re.findall(r"\S+", text)
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i+size]
        chunks.append(" ".join(chunk_words))
        i += size - overlap
        if i <= 0:
            i += size
    return chunks
