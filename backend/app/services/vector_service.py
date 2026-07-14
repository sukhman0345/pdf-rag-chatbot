import os
import pickle

import faiss
import numpy as np


from app.core.config import VECTOR_STORE_FOLDER, SIMILARITY_THRESHOLD, VECTOR_SEARCH_TOP_K

FAISS_INDEX_PATH = os.path.join(VECTOR_STORE_FOLDER, "index.faiss")
METADATA_PATH = os.path.join(VECTOR_STORE_FOLDER, "metadata.pkl")


class VectorStore:

    def __init__(self):
        self.index = None
        self.documents = []

        # Create vector_store folder if it doesn't exist
        os.makedirs(VECTOR_STORE_FOLDER, exist_ok=True)

    def create_index(self, embedded_chunks):
        """
        Create a FAISS index and save it to disk.
        """

        # Store metadata
        self.documents = [
            {
                "id": chunk["id"],
                "page": chunk["page"],
                "text": chunk["text"]
            }
            for chunk in embedded_chunks
        ]

        # Convert embeddings to NumPy array
        embeddings = np.array(
            [chunk["embedding"] for chunk in embedded_chunks],
            dtype=np.float32
        )

        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)

        # Add embeddings
        self.index.add(embeddings)

        # Save FAISS index
        faiss.write_index(self.index, FAISS_INDEX_PATH)

        # Save metadata
        with open(METADATA_PATH, "wb") as file:
            pickle.dump(self.documents, file)

    def load_index(self):
        """
        Load FAISS index and metadata from disk.
        """

        if not os.path.exists(FAISS_INDEX_PATH):
            return False

        if not os.path.exists(METADATA_PATH):
            return False

        self.index = faiss.read_index(FAISS_INDEX_PATH)

        with open(METADATA_PATH, "rb") as file:
            self.documents = pickle.load(file)

        return True

    def search(self, query_embedding, k=VECTOR_SEARCH_TOP_K):
        """
        Search the top-k most similar chunks filtering by SIMILARITY_THRESHOLD.
        """

        # Load index automatically if not loaded
        if self.index is None:
            loaded = self.load_index()

            if not loaded:
                return []

        query_embedding = np.array(
            [query_embedding],
            dtype=np.float32
        )

        distances, indices = self.index.search(query_embedding, k)

        results = []

        for dist, index in zip(distances[0], indices[0]):

            # Ignore invalid indexes
            if index == -1:
                continue

            # Calculate cosine similarity from L2 distance of normalized vectors:
            # similarity = 1 - (dist / 2)
            similarity = 1.0 - (float(dist) / 2.0)

            if similarity >= SIMILARITY_THRESHOLD:
                doc = self.documents[index].copy()
                doc["similarity_score"] = float(similarity)
                doc["cosine_distance"] = 1.0 - float(similarity)
                results.append(doc)

        return results


# Global object
vector_store = VectorStore()