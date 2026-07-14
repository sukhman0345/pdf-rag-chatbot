from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP


def create_chunks(pages):
    """
    Split extracted PDF text into smaller chunks while
    keeping the page number with each chunk.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = []

    for page in pages:

        split_text = text_splitter.split_text(page["text"])

        chunk_id = 1
          
        for chunk in split_text:

            chunks.append(
                {    
                    "id": chunk_id,
                    "page": page["page"],
                    "text": chunk
                }
            )
            chunk_id += 1

    return chunks