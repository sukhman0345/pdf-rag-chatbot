from app.services.embedding_service import get_query_embedding
from app.services.vector_service import vector_store
from app.services.llm_service import generate_response
from app.core.config import VECTOR_SEARCH_TOP_K, SIMILARITY_THRESHOLD

OUT_OF_SCOPE_MESSAGE = "This question is outside the scope of the uploaded document. Please ask questions related to the uploaded PDF only."

SYSTEM_PROMPT = (
    "You are a helpful assistant for answering questions about the uploaded PDF document.\n"
    "Your task is to answer the user's question using the provided context.\n"
    "If the provided context does not contain the answer to the question, or if the question is unrelated "
    "to the document, you MUST respond with EXACTLY this message:\n"
    f"\"{OUT_OF_SCOPE_MESSAGE}\"\n"
    "Do not assume or extrapolate. If the information is not in the context, output only the message above and nothing else."
)


def answer_query(query: str) -> dict:
    """
    Perform retrieval-augmented generation to answer the query.
    """
    # 1. Get embedding for the query
    query_embedding = get_query_embedding(query)

    # 2. Search vector store
    search_results = vector_store.search(query_embedding, k=VECTOR_SEARCH_TOP_K)

    # Debug logging
    print(f"\n[RAG Service Query Log]")
    print(f"  Query: '{query}'")
    print(f"  Similarity Threshold: {SIMILARITY_THRESHOLD}")
    print(f"  Retrieved Chunks: {len(search_results)}")
    for i, doc in enumerate(search_results):
        print(f"    Chunk #{i+1} | Page {doc['page']} | Similarity Score: {doc['similarity_score']:.4f} | Snippet: {doc['text'][:60].strip()}...")
    print(f"----------------------\n")

    # 3. If no search results passed the threshold, return the out-of-scope message
    if not search_results:
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

    # 6. Generate answer from LLM
    try:
        answer = generate_response(prompt, system_prompt=SYSTEM_PROMPT)
    except Exception as e:
        # Fallback or propagate error
        raise e

    # Clean up any wrapping quotes from LLM output if it returns the exact string with quotes
    cleaned_answer = answer.strip().strip('"').strip("'")
    if cleaned_answer == OUT_OF_SCOPE_MESSAGE:
        answer = OUT_OF_SCOPE_MESSAGE

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
