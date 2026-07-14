from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router
from app.core.config import SIMILARITY_THRESHOLD, VECTOR_SEARCH_TOP_K, LLM_MODEL, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP

app = FastAPI(title="PDF RAG Chatbot API")

# Enable CORS for frontend API consumption
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(chat_router)


@app.get("/config")
def get_config():
    return {
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "top_k": VECTOR_SEARCH_TOP_K,
        "llm_model": LLM_MODEL,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP
    }


@app.get("/")
def read_root():
    return {"message": "Hello from pdf-rag-chatbot!"}