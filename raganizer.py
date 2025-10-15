# raganizer.py
from bs4 import BeautifulSoup
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import Chroma

def clean_html(html_text):
    """Remove HTML tags and return plain text."""
    if not html_text:
        return ""
    return BeautifulSoup(html_text, "html.parser").get_text(separator="\n")

def emails_to_documents(messages):
    """Convert raw Outlook email JSON to LangChain Document objects."""
    docs = []
    for m in messages:
        subject = m.get("subject", "")
        sender = m.get("from", {}).get("emailAddress", {}).get("address", "")
        body_html = m.get("body", {}).get("content", "")
        text = clean_html(body_html)
        doc_text = f"Subject: {subject}\nFrom: {sender}\n\n{text}"
        metadata = {"subject": subject, "from": sender, "received": m.get("receivedDateTime")}
        docs.append(Document(page_content=doc_text, metadata=metadata))
    return docs

def make_or_load_chroma(docs, persist_dir="chroma_db"):
    """Embed emails and store in a persistent Chroma vector database."""
    print("🔄 Creating embeddings using HuggingFace (offline)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    chroma = Chroma.from_documents(docs, embedding=embeddings, persist_directory=persist_dir)
    chroma.persist()
    print(f"✅ Saved embeddings to {persist_dir}/")
    return chroma
