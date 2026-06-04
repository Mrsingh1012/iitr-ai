# shopkart_rag.py — minimal RAG loop for ShopKart customer support

import os  # Read environment variables like GROQ_API_KEY
import chromadb  # Vector database for storing and searching policy chunks
from sentence_transformers import SentenceTransformer  # Loads the BGE embedding model for retriever
from groq import Groq  # Client for LLM generation API calls (free, OpenAI-compatible)

# ---------------------------------------------------------------------------
# ShopKart policy records — these are our knowledge sources for this lab
# Each dict becomes one row in Chroma: id, text, metadata
# ---------------------------------------------------------------------------
POLICY_RECORDS = [
    {  # Returns policy chunk
        "id": "shopkart_returns_1",  # Unique primary key for this policy row
        "text": (
            "Unopened items may be returned within 7 calendar days of delivery. "
            "Opened or used items are not eligible unless defective."
        ),  # Human-readable returns rule — source of truth for return questions
        "metadata": {"category": "returns", "source": "returns_policy"},  # Tags for display and later filtering
    },
    {  # Shipping policy chunk
        "id": "shopkart_shipping_1",  # Unique id for shipping row
        "text": (
            "Standard delivery takes 3 to 5 business days after dispatch. "
            "Express delivery (paid) arrives in 1 to 2 business days in metro cities only."
        ),  # Shipping timelines customers ask about often
        "metadata": {"category": "shipping", "source": "shipping_policy"},  # Shipping category tag
    },
    {  # Warranty policy chunk
        "id": "shopkart_warranty_1",  # Unique id for warranty row
        "text": (
            "Electronics carry a 12-month manufacturer warranty from the date of delivery. "
            "Warranty does not cover physical damage or liquid exposure."
        ),  # Warranty coverage and exclusions
        "metadata": {"category": "warranty", "source": "warranty_policy"},  # Warranty category tag
    },
    {  # Refund policy chunk
        "id": "shopkart_refunds_1",  # Unique id for refund row
        "text": (
            "Refunds are credited within 5 to 7 business days after the returned item "
            "passes warehouse verification. Cash-on-delivery orders are refunded to the "
            "original UPI or bank account only."
        ),  # Refund timing and COD path
        "metadata": {"category": "refunds", "source": "refunds_policy"},  # Refunds category tag
    },
]

# Embedding model name — MUST stay the same for documents and every query
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # Free BGE model from Hugging Face

# LLM model name for generation — free Groq model; swap for any model Groq lists
GENERATION_MODEL_NAME = "llama-3.3-70b-versatile"  # Groq-hosted LLM used as the generator


def create_embedding_model() -> SentenceTransformer:
    # Load the local BGE embedding model once — reuse for all encode calls in this script
    return SentenceTransformer(EMBEDDING_MODEL_NAME)  # Downloads ~130MB BGE model on first run


def setup_chroma_collection():
    # Connect to on-disk Chroma storage in ./chroma_store (survives after script ends)
    client = chromadb.PersistentClient(path="./chroma_store")  # Local persistent database folder

    # Open or create the ShopKart policy collection — separate name from older demo collections
    collection = client.get_or_create_collection(
        name="shopkart_policy_kb",  # Named bucket for ShopKart policy rows
        embedding_function=None,  # We pass embeddings manually — same teaching pattern as before
    )

    return collection  # Return collection handle for upsert and query


def index_policy_records(collection, model: SentenceTransformer) -> None:
    # Build parallel lists from POLICY_RECORDS — index alignment matters for upsert
    ids = [row["id"] for row in POLICY_RECORDS]  # One unique id per policy chunk
    documents = [row["text"] for row in POLICY_RECORDS]  # Plain text stored and returned in search
    metadatas = [row["metadata"] for row in POLICY_RECORDS]  # Category and source tags per row

    # Encode all policy texts to vectors in one batch — same model as queries later
    # normalize_embeddings=True is recommended for BGE so cosine-style similarity behaves well
    embeddings = model.encode(documents, convert_to_numpy=True, normalize_embeddings=True).tolist()  # Chroma expects Python lists

    # Write all rows into Chroma — upsert is safe to rerun (updates by id if already present)
    collection.upsert(
        ids=ids,  # Primary keys
        documents=documents,  # Readable policy sentences
        metadatas=metadatas,  # Tags stored alongside each row
        embeddings=embeddings,  # Meaning vectors used for similarity search
    )

    print(f"Indexed {collection.count()} ShopKart policy records.")  # Expect 4 after first successful run


def main() -> None:
    # Load the embedding model once and reuse it for the whole run
    model = create_embedding_model()  # Local BGE encoder

    # Open (or create) the persistent Chroma collection on disk
    collection = setup_chroma_collection()  # Handle for storing/searching vectors

    # Encode every policy record and write all embeddings into ChromaDB
    index_policy_records(collection, model)  # Persists ids, documents, metadata, embeddings


if __name__ == "__main__":
    main()  # Run the indexing pipeline when this file is executed directly