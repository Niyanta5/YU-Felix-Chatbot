from functools import lru_cache
from flask import Flask, request, jsonify, send_file, session, render_template
from flask_session import Session
from flask_cors import CORS
from langchain_openai import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os
import uuid
import re
import time
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key, temperature=0)

_base_dir = os.path.dirname(os.path.abspath(__file__))
_faq_store_dir = os.path.join(_base_dir, "faq_vectorStore_grad")
faq_vectorstore = Chroma(
    persist_directory=_faq_store_dir,
    embedding_function=OpenAIEmbeddings()
)
faq_retriever = faq_vectorstore.as_retriever()

_canvas_store_dir = os.path.join(_base_dir, "Graduate_vectorStore")
canvas_vectorstore = Chroma(
    persist_directory=_canvas_store_dir,
    embedding_function=OpenAIEmbeddings()
)
canvas_retriever = canvas_vectorstore.as_retriever()

@app.route('/')
def home():
    return render_template('index.html')

def query_requests_document_or_link(query: str) -> bool:
    patterns = [
        r'\b(pdf|docx?|pptx?|xlsx?)\b',
        r'\b(download|link|file|document|resource|attachment|materials?|slides?)\b',
        r'\b(show|send|give|provide|where.*find).*(file|pdf|link|document|resource|materials?)\b',
    ]
    return any(re.search(p, query.lower()) for p in patterns)

def format_docs(docs, include_links=False):
    scraped = []
    links = []
    for doc in docs:
        content = doc.page_content.strip()
        if len(content) < 50:
            continue
        if include_links:
            found_links = re.findall(r'https?://[^\s]+', content)
            links.extend(found_links)
            if "source" in doc.metadata:
                file_name = os.path.basename(str(doc.metadata["source"]))
                links.append(f"[{file_name}](/get_file/{file_name})")
        scraped.append(content)
    joined = "\n\n".join(scraped)
    if include_links and links:
        joined += "\n\nRelevant links:\n" + "\n".join(set(links))
    return joined, links

def truncate_text_to_tokens(text, max_tokens=2500):
    return text[:max_tokens * 4]

MAX_HISTORY = 4

def format_chat_history(history):
    history = history[-MAX_HISTORY:]
    formatted = ""
    for human, assistant in history:
        formatted += f"\nUser: {human}\nFelix: {assistant}"
    return formatted

def normalize_question(text):
    """Clean and normalize input text for consistency and semantic mapping."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)

    replacements = {
        "ai ": "artificial intelligence ",
        "resume": "resume",
        "cv": "resume",
        "llm": "large language model",
        "yu": "yeshiva university",
    }

    for short, long in replacements.items():
        text = re.sub(rf"\b{re.escape(short)}\b", long, text)

    return text.strip()

@lru_cache(maxsize=1000)
def cached_llm_response(prompt):
    return llm.invoke(prompt).content

def generate_prompt(context, question, chat_history):
    return f"""You are Felix – a friendly and knowledgeable assistant designed to help students navigate [Yeshiva University's Canvas](https://yu.instructure.com) or email canvas@yu.edu.

Previous conversation history:
{chat_history}

Use the following context to answer the current question. Also, refer to the previous conversation history to infer meaning,
especially if the current message is a follow-up like "yes", "can you send it", or "please share it".
Always respond based on the most recent topic if the user does not specify a new one.

Context: {context}

Instructions:
- Ask the user if they would like the relevant link.
- Provide links only when relevant and available.
- Do not guess answers or hallucinate. Only respond based on the context.
- [MOST IMPORTANT]: If the user asks a general or irrelevant question (e.g., “can penguins fly”), do not attempt to answer it. Politely explain that you're only able to assist with topics related to Yeshiva University and Canvas support.
- If the user asks for a specific document or link, provide it directly, but only if it is relevant to their question.
- Use Markdown format for links and emails.
- Be warm, helpful, and easy to understand.
- Never use HTML anchor tags like <a> — they will break the UI.
- If someone asks who built this chatbot then answer: "This chatbot was built by Shashank, Dheeraj, Chaitanya for development, and for Azure: JK, Niyanta, Bhavitha worked."
- Ensure the history is consistently formatted and passed in every request.
- Respond in the same language that the user asked the question in.

Helpful links:
• [Yeshiva University](https://www.yu.edu)  
• [Support Services](https://www.yu.edu/student-life)  
• [Academic Calendar](https://www.yu.edu/registrar/grad-calendar)  
• [Simplicity Portal](https://yu-csm.symplicity.com/students/?signin_tab=0)  
• Help Desk: helpdesk@yu.edu  
• Career Services: careerstrategy@yu.edu  

Current Question: {question}
Response:"""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        data = request.json
        message = data['message']
        history = data.get('history', [])
        chat_history = format_chat_history(history)
        include_links = query_requests_document_or_link(message)

        all_context_parts = []
        all_links = []
        start = time.time()

        # === Retrieve from FAQ vectorstore (which includes CSV) ===
        faq_docs = faq_retriever.get_relevant_documents(message)[:8]

        # Priority 1: CSV-stored content
        csv_like_docs = [doc for doc in faq_docs if "graduate_file_metadata.csv" in doc.metadata.get("source", "").lower()]
        csv_context, csv_links = format_docs(csv_like_docs, include_links=True)

        if csv_context.strip():
            print("✅ Using CSV metadata content only.")
            all_context_parts.append("### Canvas CSV Metadata:\n" + csv_context)
            all_links.extend(csv_links)
        else:
            # Priority 2: Fallback to FAQ
            print("⚠️ No relevant content found in CSV. Falling back to FAQ.")
            faq_only_docs = [doc for doc in faq_docs if doc not in csv_like_docs]
            faq_context, faq_links = format_docs(faq_only_docs, include_links=include_links)
            if faq_context.strip():
                all_context_parts.append("### FAQ Content:\n" + faq_context)
                all_links.extend(faq_links)

        # Canvas content (separate source)
        canvas_docs = canvas_retriever.get_relevant_documents(message)[:5]
        print(f"📘 Canvas documents retrieved: {[doc.metadata.get('source', '') for doc in canvas_docs]}")
        canvas_context, canvas_links = format_docs(canvas_docs, include_links=include_links)
        if canvas_context.strip():
            all_context_parts.append("### Canvas Content:\n" + canvas_context)
            all_links.extend(canvas_links)

        # If nothing relevant found anywhere
        if not all_context_parts:
            print("❌ No relevant context found.")
            return jsonify({
                "response": "I'm here to help with Yeshiva University resources and Canvas support. Unfortunately, I couldn't find anything related to your question.",
                "links": []
            })

        final_context = "\n\n".join(all_context_parts)
        final_context = truncate_text_to_tokens(final_context)

        normalized_question = normalize_question(message)
        prompt = generate_prompt(final_context, normalized_question, chat_history)
        response = cached_llm_response(prompt)

        print(f"⏱️ Total time to respond: {round(time.time() - start, 2)}s")

        return jsonify({
            'response': response,
            'source': "csv_first_priority",
            'links': list(set(all_links))
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_file/<filename>', methods=['GET'])
def get_file(filename):
    try:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(path):
            return jsonify({'error': 'File not found'}), 404
        return send_file(path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

