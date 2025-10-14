# test_qa.py — Interactive test runner for intelligent email QA
from qa import load_qa_chain, smart_answer

if __name__ == "__main__":
    qa, retriever, llm, db = load_qa_chain()

    print("\n🧠 Smart Email QA Assistant is ready!")
    print("Type a question like:\n")
    print(" • what is my latest email?")
    print(" • show me emails from GIKI")
    print(" • emails between July and September")
    print(" • how many emails did I get today?\n")

    while True:
        query = input("💬 Ask a question (or type 'exit'): ").strip()
        if query.lower() == "exit":
            print("👋 Exiting Smart Email QA. Goodbye!")
            break

        if not query:
            print("⚠️ Please enter a valid question.")
            continue

        print("\n🔎 Thinking...\n")
        try:
            answer = smart_answer(query, retriever, llm)
            print("🤖 Answer:\n" + answer + "\n")
        except Exception as e:
            print(f"❌ Error while processing: {e}\n")






