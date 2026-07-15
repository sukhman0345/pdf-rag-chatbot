from app.services.embedding_service import get_query_embedding
from app.services.vector_service import vector_store
from app.services.llm_service import generate_response
from app.core.config import VECTOR_SEARCH_TOP_K, SIMILARITY_THRESHOLD

OUT_OF_SCOPE_MESSAGE = "This question is outside the scope of the uploaded document. Please ask questions related to the uploaded PDF only."

SYSTEM_PROMPT = (
    "You are a helpful assistant for answering questions about the uploaded PDF document.\n"
    "Your task is to answer the user's question using the provided context.\n"
    "If the uploaded document is a resume, CV, portfolio, or personal profile, assume that the user is the subject of the document. "
    "Therefore, when the user asks questions using first-person pronouns (e.g., 'my name', 'my experience', 'who am I'), "
    "answer using the information about the person described in the document.\n"
    "If the provided context does not contain the answer to the question, or if the question is unrelated "
    "to the document, you MUST respond with EXACTLY this message:\n"
    f"\"{OUT_OF_SCOPE_MESSAGE}\"\n"
    "Do not assume or extrapolate. If the information is not in the context, output only the message above and nothing else."
)


import uuid

# Memory storage: session_id -> list of message dicts
sessions_memory = {}


def create_session() -> str:
    """
    Generate a new unique session_id and initialize its memory history.
    """
    session_id = str(uuid.uuid4())
    sessions_memory[session_id] = []
    return session_id


def answer_query(query: str, session_id: str) -> dict:
    """
    Perform retrieval-augmented generation to answer the query.
    """
    # Get or initialize history
    if session_id not in sessions_memory:
        sessions_memory[session_id] = []
    history = sessions_memory[session_id]

    # 1. Get embedding for the query
    query_embedding = get_query_embedding(query)

    # 2. Search vector store
    search_results = vector_store.search(query_embedding, k=VECTOR_SEARCH_TOP_K)

    # Debug logging
    print(f"\n[RAG Service Query Log]")
    print(f"  Session ID: {session_id}")
    print(f"  Query: '{query}'")
    print(f"  Similarity Threshold: {SIMILARITY_THRESHOLD}")
    print(f"  Retrieved Chunks: {len(search_results)}")
    for i, doc in enumerate(search_results):
        print(f"    Chunk #{i+1} | Page {doc['page']} | Similarity Score: {doc['similarity_score']:.4f} | Snippet: {doc['text'][:60].strip()}...")
    print(f"----------------------\n")

    # 3. If no search results passed the threshold, return the out-of-scope message
    if not search_results:
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": OUT_OF_SCOPE_MESSAGE})
        return {
            "answer": OUT_OF_SCOPE_MESSAGE,
            "sources": []
        }

    # 4. Construct context
    context_parts = []
    for doc in search_results:
        context_parts.append(f"Page {doc['page']}: {doc['text']}")
    
    context = "\n\n".join(context_parts)

    # 5. Format prompt
    prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    # 6. Generate answer from LLM with memory history
    try:
        answer = generate_response(prompt, system_prompt=SYSTEM_PROMPT, history=history)
    except Exception as e:
        raise e

    # Clean up any wrapping quotes from LLM output if it returns the exact string with quotes
    cleaned_answer = answer.strip().strip('"').strip("'")
    if cleaned_answer == OUT_OF_SCOPE_MESSAGE:
        answer = OUT_OF_SCOPE_MESSAGE

    # Save to history
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})

    # 7. Format sources with metrics
    sources = []
    if answer != OUT_OF_SCOPE_MESSAGE:
        for doc in search_results:
            sources.append({
                "page": doc["page"],
                "text": doc["text"],
                "similarity_score": doc["similarity_score"],
                "cosine_distance": doc["cosine_distance"]
            })

    return {
        "answer": answer,
        "sources": sources
    }
