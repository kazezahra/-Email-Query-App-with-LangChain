import os
from datetime import datetime, timedelta
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# --- Load embeddings + DB ---
def load_qa_chain(persist_dir="chroma_db_test"):
    print("🔍 Loading Chroma DB and embeddings...")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 8})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    print("✅ QA system ready.\n")
    return qa, retriever, llm, db


# --- Intelligent answering logic ---
def smart_answer(query, retriever, llm):
    query_lower = query.lower()
    docs = retriever.get_relevant_documents(query)
    now = datetime.utcnow()

    # --- 1. COUNTING FEATURES ---
    if "how many" in query_lower or "count" in query_lower:
        count = 0
        matched_docs = []

        # Handle "today", "yesterday", "week", "month"
        for d in docs:
            received = d.metadata.get("received")
            if not received:
                continue
            try:
                dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
            except:
                continue

            if "today" in query_lower and dt.date() == now.date():
                count += 1
                matched_docs.append(d)
            elif "yesterday" in query_lower and dt.date() == (now - timedelta(days=1)).date():
                count += 1
                matched_docs.append(d)
            elif "week" in query_lower and dt.date() >= (now - timedelta(days=7)).date():
                count += 1
                matched_docs.append(d)
            elif "month" in query_lower and dt.month == now.month:
                count += 1
                matched_docs.append(d)

        if count > 0:
            senders = list({doc.metadata.get("from", "unknown") for doc in matched_docs})
            senders_list = ", ".join(senders[:5]) + ("..." if len(senders) > 5 else "")
            return f"📬 You received {count} email(s). Some senders include: {senders_list}"
        else:
            return "📭 You didn’t receive any emails matching that timeframe."

    # --- 2. FILTER BY DOMAIN ---
    if "giki" in query_lower:
        giki_docs = [d for d in docs if "giki.edu.pk" in str(d.metadata.get("from", "")).lower()]
        if giki_docs:
            result = "\n".join(
                [
                    f"From: {d.metadata.get('from')}\nSubject: {d.metadata.get('subject')}\nReceived: {d.metadata.get('received')}\n"
                    for d in giki_docs[:5]
                ]
            )
            return f"📧 Emails from GIKI:\n{result}"
        return "No GIKI emails found."

    # --- 3. FILTER BY DATE RANGE (months) ---
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }

    found_months = [m for m in months if m in query_lower]
    if found_months:
        month_nums = [months[m] for m in found_months]
        month_docs = [
            d for d in docs
            if d.metadata.get("received") and datetime.fromisoformat(
                d.metadata["received"].replace("Z", "+00:00")
            ).month in month_nums
        ]
        if month_docs:
            result = "\n".join(
                [
                    f"From: {d.metadata.get('from')}\nSubject: {d.metadata.get('subject')}\nReceived: {d.metadata.get('received')}\n"
                    for d in month_docs[:8]
                ]
            )
            return f"📬 Emails between {' and '.join(found_months)} — found {len(month_docs)} result(s):\n\n{result}"
        return f"No emails found between {' and '.join(found_months)}."

    # --- 4. LOST & FOUND / keyword search ---
    if "lost" in query_lower or "found" in query_lower:
        lf_docs = [
            d for d in docs if "lost" in d.page_content.lower() or "found" in d.page_content.lower()
        ]
        if lf_docs:
            result = "\n".join(
                [
                    f"From: {d.metadata.get('from')}\nSubject: {d.metadata.get('subject')}\nReceived: {d.metadata.get('received')}\n"
                    for d in lf_docs[:5]
                ]
            )
            return f"📦 Lost & Found related emails:\n{result}"
        return "No lost or found related emails found."

    # --- 5. GENERAL QUERY ---
    if "latest" in query_lower or "recent" in query_lower:
        if docs:
            latest = sorted(
                [d for d in docs if d.metadata.get("received")],
                key=lambda x: x.metadata["received"],
                reverse=True,
            )[0]
            return (
                f"Latest email was from {latest.metadata.get('from')} "
                f"with subject '{latest.metadata.get('subject')}' "
                f"received on {latest.metadata.get('received')}."
            )
        return "I couldn’t find any recent emails."

    # --- 6. Default to LLM reasoning ---
    result = llm.invoke(f"Answer based on these email snippets: {docs}\n\nQuestion: {query}")
    return result.content.strip() if hasattr(result, "content") else str(result)
