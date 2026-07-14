# PDF RAG Chatbot

A modern, high-performance Retrieval-Augmented Generation (RAG) application with a split architecture: a **FastAPI backend** (using FAISS, Sentence Transformers, and Groq Cloud API) and a **sleek responsive HTML/CSS/JS frontend**. This project allows users to upload a PDF document, automatically chunks and embeds the content, stores it in a local vector database, and lets users ask questions strictly related to the PDF with real-time similarity metrics and page citations.

---

## Directory Structure

```text
pdf-rag-chatbot/
├── backend/                  # FastAPI Backend Server
│   ├── app/
│   │   ├── api/              # Upload and Chat endpoints
│   │   ├── core/             # App configs (.env loader)
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # PDF parser, embedding, vector search, LLM, and RAG logic
│   │   └── utils/            # Recursive character chunking
│   ├── main.py               # Main API application entry point (with CORS enabled)
│   ├── requirements.txt      # Backend Python dependencies
│   ├── pyproject.toml
│   └── .env                  # Configuration variables (keys, thresholds)
│
├── frontend/                 # Interactive SPA Client
│   ├── index.html            # Sidebar and chat views
│   ├── style.css             # Premium custom dark-mode styling
│   └── app.js                # XHR upload progress tracker & API handler
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python >= 3.11)
- **Vector Search**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLM API Provider**: Groq SDK
- **PDF Parser**: PyMuPDF (`fitz`)
- **Text Chunking**: LangChain Text Splitters

### Frontend
- **Structure**: Vanilla HTML5 (semantic elements)
- **Styling**: Vanilla CSS3 (custom variables, glassmorphism, flexbox/grid layout, responsive design)
- **Icons**: FontAwesome v6
- **Fonts**: Google Fonts (Outfit)
- **Logic**: Vanilla ES6 JavaScript (includes real-time XHR upload progress tracking)

---

## Setup & Running

### 1. Start the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install the dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend` directory (if it does not exist) and configure your keys and thresholds:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
   SIMILARITY_THRESHOLD=0.2
   LLM_MODEL=llama-3.3-70b-specdec
   LLM_TEMPERATURE=0.7
   VECTOR_SEARCH_TOP_K=5
   CHUNK_SIZE=500
   CHUNK_OVERLAP=100
   ```
4. Start the backend ASGI server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend interactive documentation will be available at **http://127.0.0.1:8000/docs**.

---

### 2. Start the Frontend

CORS (Cross-Origin Resource Sharing) is enabled on the FastAPI backend, allowing the frontend to communicate with it from any origin.

To launch the UI:
1. Simply double-click **`frontend/index.html`** to open it in your preferred web browser.
2. Drag and drop any PDF file to upload and start querying!

---

## API Endpoints & Demo Payloads

### 1. Upload PDF
Uploads and indexes a PDF.

* **Endpoint**: `POST http://127.0.0.1:8000/upload`
* **Content-Type**: `multipart/form-data`
* **Response Payload**:
  ```json
  {
    "message": "PDF uploaded successfully.",
    "filename": "annual_report.pdf",
    "total_pages": 12,
    "total_chunks": 48,
    "total_embeddings": 48
  }
  ```

---

### 2. Chat with PDF
Query the chatbot on content from the uploaded PDF document.

* **Endpoint**: `POST http://127.0.0.1:8000/chat`
* **Content-Type**: `application/json`
* **Request Payload**:
  ```json
  {
    "query": "What were the total profits in 2025?"
  }
  ```

#### Demo Response (Within Scope):
```json
{
  "answer": "According to the annual report, the total profits in 2025 were $4.2 million, showing a 15% increase compared to 2024.",
  "sources": [
    {
      "page": 3,
      "text": "Financial Summary: Net profits for the fiscal year ending 2025 rose to $4.2 million from $3.65 million in 2024...",
      "similarity_score": 0.7845,
      "cosine_distance": 0.2155
    },
    {
      "page": 4,
      "text": "Profit margins in 2025 stabilized due to strong product uptake...",
      "similarity_score": 0.6512,
      "cosine_distance": 0.3488
    }
  ]
}
```

#### Demo Response (Out of Scope / Empty Vector DB):
```json
{
  "answer": "This question is outside the scope of the uploaded document. Please ask questions related to the uploaded PDF only.",
  "sources": []
}
```
