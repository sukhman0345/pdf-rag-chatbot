from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_service import extract_text_from_pdf
from app.services.embedding_service import create_embeddings
from app.utils.chunking import create_chunks
from app.services.vector_service import vector_store
from app.services.rag_service import create_session
import shutil
import os

from app.core.config import UPLOAD_FOLDER

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)


@router.post("")
async def upload_pdf(file: UploadFile = File(...)):
    # Check if the uploaded file is a PDF
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # Create the file path
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process the PDF and build vector store index
    pages = extract_text_from_pdf(file_path)
    chunks = create_chunks(pages)
    embedded_chunks = create_embeddings(chunks)
    vector_store.create_index(embedded_chunks)

    session_id = create_session()

    return {
        "message": "PDF uploaded successfully.",
        "filename": file.filename,
        "total_pages": len(pages),
        "total_chunks": len(chunks),
        "total_embeddings": len(embedded_chunks),
        "session_id": session_id
    } 