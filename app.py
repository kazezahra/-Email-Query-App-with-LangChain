# app.py — Streamlit UI for Outlook → LangChain email Q&A
import os
import json
import streamlit as st
from datetime import datetime, date
from dotenv import load_dotenv

# Load .env (optional)
load_dotenv()

# Local helper modules (from your project)
from auth_utils import get_access_token
from graph_utils import list_messages
from raganizer import emails_to_documents, make_or_load_chroma
from qa import load_qa_chain, smart_answer

st.set_page_config(page_title="Outlook Email QA", layout="wide")

# ---- Sidebar: Sign-in + settings ----
st.sidebar.title("Settings & Login")

if "token" not in st.session_state:
    st.session_state["token"] = None

if "emails" not in st.session_state:
    st.session_state["emails"] = []

if "docs" not in st.session_state:
    st.session_state["docs"] = []

if "chroma_dir" not in st.session_state:
    st.session_state["chroma_dir"] = None

if "qa_objs" not in st.session_state:
    st.session_state["qa_objs"] = None  # will hold (qa, retriever, llm, db)

st.sidebar.markdown("### Azure / App settings")
st.sidebar.write("Client/Tenant read from environment or `.env`")

st.sidebar.markdown("---")
st.sidebar.markdown("### Fetch options")
top_default = 200
top_val = st.sidebar.number_input(
    "Max emails to fetch (top)", min_value=20, max_value=2000, value=top_default, step=20
)

# Sign in button
if st.sidebar.button("Sign in (device code)"):
    try:
        token = get_access_token()
        st.session_state["token"] = token
        st.sidebar.success("Signed in — token cached.")
    except Exception as e:
        st.sidebar.error(f"Sign in failed: {e}")

if st.session_state["token"]:
    st.sidebar.info("Signed in ✓")
else:
    st.sidebar.warning("Not signed in — click Sign in above")

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ — Kaz")
st.sidebar.caption("Tip: choose a date and click Fetch emails")

# ---- Main layout ----
st.title("📧 Outlook Email Q&A (LangChain + Chroma)")

col1, col2 = st.columns([2, 3])

# ---------------- LEFT COLUMN ----------------
with col1:
    st.header("1️⃣ Select date & fetch")
    pick_date = st.date_input("Choose date (UTC) to fetch emails from", value=date.today())
    pick_date_str = pick_date.isoformat()

    if st.button("📨 Fetch emails for this date"):
        if not st.session_state["token"]:
            st.error("You must sign in first (see sidebar).")
        else:
            with st.spinner("Fetching emails from Outlook..."):
                try:
                    all_msgs = list_messages(st.session_state["token"], top=top_val)
                except Exception as e:
                    st.error(f"Error fetching emails: {e}")
                    all_msgs = []

                filtered = [
                    m for m in all_msgs if m.get("receivedDateTime", "").startswith(pick_date_str)
                ]
                st.session_state["emails"] = filtered
                st.success(f"📬 Fetched {len(filtered)} messages for {pick_date_str}")

    # quick summary / preview
    if st.session_state["emails"]:
        st.markdown("**Preview of fetched emails (first 10)**")
        for i, m in enumerate(st.session_state["emails"][:10]):
            subject = m.get("subject", "(no subject)")
            sender = m.get("from", {}).get("emailAddress", {}).get("address", "")
            received = m.get("receivedDateTime", "")
            st.write(f"**{i+1}.** {subject} — `{sender}` — {received}")

        # ✅ FIXED block — auto-refreshes after embedding
        if st.button("🧠 Index these emails (create embeddings & Chroma)"):
            with st.spinner("Creating documents & embeddings... (this may take a while)"):
                try:
                    docs = emails_to_documents(st.session_state["emails"])
                    persist_dir = f"chroma_db_{pick_date_str}"
                    st.session_state["chroma_dir"] = persist_dir
                    make_or_load_chroma(docs, persist_dir=persist_dir)
                    st.success("✅ Indexing complete. Ready for QA.")
                    st.toast("Reloading UI to activate Q&A...", icon="🔄")
                    st.rerun()
                except Exception as e:
                    st.error(f"Indexing failed: {e}")
    else:
        st.info("No fetched emails yet. Pick a date and click 'Fetch emails'.")

# ---------------- RIGHT COLUMN ----------------
with col2:
    st.header("2️⃣ Ask questions (natural language)")
    st.caption(f"Active Chroma DB: {st.session_state.get('chroma_dir', 'None')}")

    if st.session_state.get("chroma_dir") is None:
        st.info("⚠️ Index a date's emails first (left column).")
    else:
        # Load QA chain (if not already loaded)
        if st.session_state["qa_objs"] is None:
            with st.spinner("Loading QA chain and retriever..."):
                try:
                    qa, retriever, llm, db = load_qa_chain(persist_dir=st.session_state["chroma_dir"])
                    st.session_state["qa_objs"] = (qa, retriever, llm, db)
                    st.success("✅ QA chain loaded.")
                except Exception as e:
                    st.error(f"Failed to load QA chain: {e}")
                    st.session_state["qa_objs"] = None

        if st.session_state["qa_objs"]:
            qa, retriever, llm, db = st.session_state["qa_objs"]
            query = st.text_area("💬 Ask a question about today's emails", height=120)

            colq1, colq2 = st.columns([1, 1])
            with colq1:
                if st.button("🚀 Ask"):
                    if not query.strip():
                        st.warning("Type a question first.")
                    else:
                        with st.spinner("🤔 Thinking..."):
                            try:
                                answer = smart_answer(query, retriever, llm)
                                st.markdown("### 🤖 Answer:")
                                st.write(answer)
                            except Exception as e:
                                st.error(f"Error while answering: {e}")
            with colq2:
                if st.button("📄 Show top retrieved docs"):
                    with st.spinner("Retrieving top docs..."):
                        try:
                            hits = retriever.get_relevant_documents(query or "summary")
                            st.markdown("### Top retrieved documents")
                            for i, h in enumerate(hits[:8], 1):
                                st.write(
                                    f"**{i}.** From: `{h.metadata.get('from')}` — "
                                    f"Subject: **{h.metadata.get('subject')}** — "
                                    f"Received: `{h.metadata.get('received')}`"
                                )
                                snippet = (h.page_content or "")[:500].replace("\n", " ")
                                st.caption(snippet)
                        except Exception as e:
                            st.error(f"Error retrieving docs: {e}")

# ---------------- BOTTOM SECTION ----------------
st.markdown("---")
col_a, col_b = st.columns([1, 1])

with col_a:
    st.header("💾 Export & Save")
    if st.session_state.get("emails"):
        data = json.dumps(st.session_state["emails"], indent=2)
        st.download_button(
            "⬇️ Download fetched emails (JSON)",
            data=data,
            file_name=f"emails_{pick_date_str}.json",
            mime="application/json",
        )

with col_b:
    st.header("🧩 Debug / Info")
    if st.button("Show session info"):
        st.write({
            "token_present": bool(st.session_state.get("token")),
            "num_fetched_emails": len(st.session_state.get("emails", [])),
            "chroma_dir": st.session_state.get("chroma_dir"),
            "qa_loaded": bool(st.session_state.get("qa_objs")),
        })

st.markdown("""
**Notes:**
- Embeddings are stored in the folder named `chroma_db_<date>`.
- Use the sidebar **Sign in** button to authenticate via device code.
- If embedding many emails, it may take a few minutes — please wait patiently.
""")
