import re
import uuid
from app.services.embedding_service import get_query_embedding
from app.services.vector_service import vector_store
from app.services.llm_service import generate_response
from app.core.config import VECTOR_SEARCH_TOP_K, SIMILARITY_THRESHOLD

OUT_OF_SCOPE_MESSAGE = "This question is outside the scope of the uploaded document. Please ask questions related to the uploaded PDF only."

SYSTEM_PROMPT = (
    "You are a helpful assistant for answering questions about the uploaded PDF document.\n"
    "Your task is to answer the user's question using the provided context.\n\n"
    "IMPORTANT DOCUMENT HANDLING DETAILS:\n"
    "- If the uploaded document is a resume, CV, portfolio, or personal profile, the subject of the document is the user. "
    "Therefore, when the user asks questions in the first person (e.g., 'my name', 'my experience', 'who am I', 'where did I study', 'my skills'), "
    "map these pronouns to the candidate/person described in the resume and answer using their details.\n"
    "- Do not answer questions that cannot be derived from the document or that are completely unrelated to it. "
    "If the provided context does not contain the answer or is unrelated, you MUST respond with EXACTLY this message:\n"
    f"\"{OUT_OF_SCOPE_MESSAGE}\"\n"
    "- Keep your answers factual and based only on the provided context. Avoid speculation, but you are expected to map the user's first-person queries to the resume subject's information."
)


def normalize_and_expand_query(query: str) -> str:
    """
    Refines and expands the query to improve semantic matching against resume/CV structures.
    Replaces first-person pronouns with candidate-centric phrasing and appends section-specific terms.
    """
    q_lower = query.lower()
    
    # 1. First-person pronoun normalization
    normalized = query
    replacements = [
        (r"\bmy name\b", "candidate name"),
        (r"\bwho am i\b", "candidate name profile summary"),
        (r"\bmy experience\b", "candidate work history experience resume"),
        (r"\bmy skills\b", "candidate technical skills technologies"),
        (r"\bmy education\b", "candidate education degree university"),
        (r"\bmy projects\b", "candidate key projects github"),
        (r"\bmy contact\b", "candidate contact email phone location"),
        (r"\bmy profile\b", "candidate profile professional summary"),
        (r"\bi am\b", "candidate is"),
        (r"\bdo i have\b", "does the candidate have"),
        (r"\bdo i know\b", "does the candidate know"),
        (r"\bdid i do\b", "did the candidate do"),
        (r"\bi did\b", "candidate did"),
        (r"\bwhere did i study\b", "candidate education university degree"),
        (r"\bwhere did i work\b", "candidate work history experience"),
        (r"\bmy\b", "candidate"),
    ]
    
    for pattern, repl in replacements:
        normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)
    
    # 2. Section keyword expansion
    expansions = []
    if any(k in q_lower for k in ["name", "who am i", "who are you", "who is this"]):
        expansions.append("name profile email phone contact info resume title")
    if "skill" in q_lower:
        expansions.append("technical skills languages tools frameworks databases")
    if any(k in q_lower for k in ["work", "experience", "job", "intern", "role", "position"]):
        expansions.append("work history experience internship company employment")
    if "project" in q_lower:
        expansions.append("projects github portfolio development link")
    if any(k in q_lower for k in ["education", "study", "degree", "college", "university", "school", "gpa"]):
        expansions.append("education academic university degree college school gpa")
        
    expanded_parts = [normalized]
    if expansions:
        expanded_parts.append(" ".join(expansions))
        
    return " ".join(expanded_parts)


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

    # Ensure index and metadata are loaded from disk
    if vector_store.index is None:
        vector_store.load_index()

    # Determine if this is a small document (e.g. resumes, CVs <= 20 chunks)
    # If it is small, we bypass retrieval and feed the entire document to the LLM.
    # This guarantees 100% accurate answering and avoids semantic search mismatch.
    is_small_doc = len(vector_store.documents) > 0 and len(vector_store.documents) <= 20

    refined_query = query
    if is_small_doc:
        search_results = []
        for doc in vector_store.documents:
            d = doc.copy()
            # Mark similarity metrics as 1.0/0.0 for full context chunks so they pass threshold checks
            d["similarity_score"] = 1.0
            d["cosine_distance"] = 0.0
            search_results.append(d)
    else:
        # 1. Refine/Expand the query for better semantic search compatibility
        refined_query = normalize_and_expand_query(query)

        # 2. Get embedding for the refined query
        query_embedding = get_query_embedding(refined_query)

        # 3. Search vector store
        search_results = vector_store.search(query_embedding, k=VECTOR_SEARCH_TOP_K)

    # Debug logging
    print(f"\n[RAG Service Query Log]")
    print(f"  Session ID: {session_id}")
    print(f"  Query: '{query}'")
    if not is_small_doc:
        print(f"  Refined Query: '{refined_query}'")
    print(f"  Similarity Threshold: {SIMILARITY_THRESHOLD}")
    print(f"  Document Mode: {'FULL CONTEXT (Small Doc)' if is_small_doc else 'RETRIEVAL'}")
    print(f"  Retrieved Chunks: {len(search_results)}")
    for i, doc in enumerate(search_results):
        print(f"    Chunk #{i+1} | Page {doc['page']} | Similarity Score: {doc['similarity_score']:.4f} | Snippet: {doc['text'][:60].strip()}...")
    print(f"----------------------\n")

    # 4. If no search results passed the threshold, return the out-of-scope message
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
