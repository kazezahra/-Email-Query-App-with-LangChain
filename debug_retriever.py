# debug_retriever.py
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

PERSIST_DIR = "chroma_db_test"  # change if you used a different folder
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def debug_query(query, k=5):
    print("Loading embeddings and Chroma DB...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": k})

    print(f"\nRunning retrieval for query: {query!r} (k={k})\n")
    docs = retriever.get_relevant_documents(query)

    print(f"Retrieved {len(docs)} documents.\n")
    for i, d in enumerate(docs, 1):
        # show metadata and beginning of content
        print(f"--- Doc #{i} ---")
        md = d.metadata or {}
        print("metadata:", md)
        snippet = d.page_content[:500].replace("\n", " ")
        print("content snippet:", snippet)
        print()

if __name__ == "__main__":
    # Replace this with the same phrase you tried in test_qa.py
    debug_query("what is my latest email?", k=8)
    # try a date / simple fact query:
    debug_query("how many mails have i gotten today?", k=8)
