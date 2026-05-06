import datetime
from functools import lru_cache
import fitz
from flask import Flask, json, request, jsonify, send_file, session, render_template
from docx import Document
from werkzeug.utils import secure_filename
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
from azure.storage.blob import BlobServiceClient

# === Load environment variables ===
load_dotenv()

app = Flask(__name__, template_folder="templates")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key, temperature=0)

# Vectorstore directories (always load from Web subfolder, regardless of CWD)
_base_dir = os.path.dirname(os.path.abspath(__file__))
_faq_store_dir = os.path.join(_base_dir, "faq_vectorStore")
_canvas_store_dir = os.path.join(_base_dir, "undergraduate_vectorStore")

faq_vectorstore = Chroma(
    persist_directory=_faq_store_dir,
    embedding_function=OpenAIEmbeddings()
)
faq_retriever = faq_vectorstore.as_retriever()

canvas_vectorstore = Chroma(
    persist_directory=_canvas_store_dir,
    embedding_function=OpenAIEmbeddings()
)
canvas_retriever = canvas_vectorstore.as_retriever()

# === Azure Logging ===
AZURE_LOG_CONTAINER = "canvas-logs"
AZURE_LOG_CONNECTION_STRING = os.getenv("AZURE_LOG_CONNECTION_STRING")  # Best practice


def sanitize_email(email):
    if not email:
        return "unknown"
    return email.replace("@", "_at_").replace(".", "_").lower()


def log_chat_to_blob(
    user_input,
    response_text,
    session_id,
    source,
    context,
    history,
    email="unknown-user",
):
    try:
        blob_service = BlobServiceClient.from_connection_string(
            AZURE_LOG_CONNECTION_STRING
        )
        container_client = blob_service.get_container_client(AZURE_LOG_CONTAINER)
        # Removed container creation per user instruction

        email_folder = sanitize_email(email or "unknown")
        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
        timestamp = datetime.utcnow().isoformat()
        safe_session = str(session_id or "no-session")

        log_entry = {
            "timestamp": timestamp,
            "session_id": safe_session,
            "user_email": email,
            "user_message": user_input,
            "chatbot_response": response_text,
            "vector_source": source,
            "context_used": context,
            "chat_history": history,
        }

        blob_name = f"{email_folder}/{date_prefix}/{safe_session}/{timestamp}_chat.txt"
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(str(log_entry), overwrite=True)

    except Exception as e:
        print(f"⚠️ Logging failed: {e}")


def log_error_to_blob(session_id, error, user_input=None, email="unknown-user"):
    try:
        blob_service = BlobServiceClient.from_connection_string(
            AZURE_LOG_CONNECTION_STRING
        )
        container_client = blob_service.get_container_client(AZURE_LOG_CONTAINER)
        # Removed container creation per user instruction

        email_folder = sanitize_email(email or "unknown")
        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
        timestamp = datetime.utcnow().isoformat()
        safe_session = str(session_id or "no-session")

        error_entry = {
            "timestamp": timestamp,
            "session_id": safe_session,
            "user_email": email,
            "user_message": user_input,
            "error": str(error),
        }

        blob_name = f"{email_folder}/{date_prefix}/{safe_session}/{timestamp}_error.txt"
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(json.dumps(error_entry, indent=2), overwrite=True)

    except Exception as e:
        print(f"❌ Failed to log error to blob: {e}")


@app.route("/")
def home():
    return render_template("index.html")


def query_requests_document_or_link(query: str) -> bool:
    patterns = [
        r"\b(pdf|docx?|pptx?|xlsx?)\b",
        r"\b(download|link|file|document|resource|attachment|materials?|slides?)\b",
        r"\b(show|send|give|provide|where.*find).*(file|pdf|link|document|resource|materials?)\b",
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
            found_links = re.findall(r"https?://[^\s]+", content)
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
    return text[: max_tokens * 4]


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
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)

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
- Chatbot response should be well-structured and clear.
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


@app.route("/chat", methods=["POST"])
def chat():
    try:
        if "session_id" not in session:
            session["session_id"] = str(uuid.uuid4())

        data = request.json
        message = data["message"]
        history = data.get("history", [])
        chat_history = format_chat_history(history)
        include_links = query_requests_document_or_link(message)

        all_context_parts = []
        all_links = []
        start = time.time()

        # === Retrieve from FAQ vectorstore (which includes CSV) ===
        faq_docs = faq_retriever.get_relevant_documents(message)[:8]

        # Priority 1: CSV-stored content
        csv_like_docs = [
            doc
            for doc in faq_docs
            if "yeshiva_undergraduate_canvas.csv"
            in doc.metadata.get("source", "").lower()
        ]
        csv_context, csv_links = format_docs(csv_like_docs, include_links=True)

        if csv_context.strip():
            print("✅ Using CSV metadata content only.")
            all_context_parts.append("### Canvas CSV Metadata:\n" + csv_context)
            all_links.extend(csv_links)
        else:
            # Priority 2: Fallback to FAQ
            print("⚠️ No relevant content found in CSV. Falling back to FAQ.")
            faq_only_docs = [doc for doc in faq_docs if doc not in csv_like_docs]
            faq_context, faq_links = format_docs(
                faq_only_docs, include_links=include_links
            )
            if faq_context.strip():
                all_context_parts.append("### FAQ Content:\n" + faq_context)
                all_links.extend(faq_links)

        # Canvas content (separate source)
        canvas_docs = canvas_retriever.get_relevant_documents(message)[:5]
        print(
            f"📘 Canvas documents retrieved: {[doc.metadata.get('source', '') for doc in canvas_docs]}"
        )
        canvas_context, canvas_links = format_docs(
            canvas_docs, include_links=include_links
        )
        if canvas_context.strip():
            all_context_parts.append("### Canvas Content:\n" + canvas_context)
            all_links.extend(canvas_links)

        # If nothing relevant found anywhere
        if not all_context_parts:
            print("❌ No relevant context found.")
            return jsonify(
                {
                    # yeshiva university should be changed. need information from anagh or susan
                    "response": "I'm here to help with Yeshiva University resources and Canvas support. Unfortunately, I couldn't find anything related to your question.",
                    "links": [],
                }
            )

        final_context = "\n\n".join(all_context_parts)
        final_context = truncate_text_to_tokens(final_context)

        normalized_question = normalize_question(message)
        prompt = generate_prompt(final_context, normalized_question, chat_history)
        response = cached_llm_response(prompt)

        print(f"⏱️ Total time to respond: {round(time.time() - start, 2)}s")

        return jsonify(
            {
                "response": response,
                "source": "csv_first_priority",
                "links": list(set(all_links)),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from docx import Document as DocxDocument


@app.route("/upload_review", methods=["POST"])
def upload_review():
    try:
        if "session_id" not in session:
            session["session_id"] = str(uuid.uuid4())
        if "review_history" not in session:
            session["review_history"] = []

        file = request.files.get("file")
        doc_type = request.form.get("type", "resume")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(upload_path)

        # === Extract Text ===
        text = ""
        if filename.lower().endswith(".pdf"):
            with fitz.open(upload_path) as doc:
                text = "".join([page.get_text() for page in doc])
        elif filename.lower().endswith(".docx"):
            doc = DocxDocument(upload_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif filename.lower().endswith(".txt"):
            with open(upload_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            return jsonify({"error": "Unsupported file format"}), 400

        os.remove(upload_path)

        if not text.strip():
            return jsonify({"error": "No content found in the document."}), 400

        # Truncate to reduce token load (~4 characters = 1 token)
        safe_text = text[:5000]

        # === Query both vectorstores ===
        faq_matches = faq_vectorstore.similarity_search(safe_text, k=3)
        canvas_matches = canvas_vectorstore.similarity_search(safe_text, k=3)
        all_matches = faq_matches + canvas_matches

        if not all_matches:
            return jsonify(
                {
                    "response": "This document doesn't appear relevant to any known job role or academic content. Please upload a resume or cover letter targeting a specific role."
                }
            )

        comparison_context = "\n\n---\n\n".join(
            [doc.page_content for doc in all_matches]
        )[:4000]
        history = "\n\n".join(session["review_history"][-3:])

        # === Structured Prompt ===
        prompt = f"""
You are a career advisor and resume expert helping users tailor job application documents like resumes and cover letters for maximum impact.

Your tasks:
1. Determine if the uploaded document is a resume or a cover letter. If not, politely inform the user you cannot assist with the file.
2. Based on the text content, infer the most likely job role or field the user is targeting (e.g., AI/ML, Web Development, Cybersecurity, Data Analytics, etc).
3. Compare the user's content with the reference examples provided below to validate consistency and completeness.
4. Provide detailed feedback to improve the document, including:
   - Strengths
   - Areas for Improvement
   - Formatting or clarity suggestions
   - Missing elements or opportunities
5. If the document is unrelated to job applications, such as course material, notes, or essays, politely explain it is not a valid resume or cover letter and do not hallucinate suggestions.
6. Ask: "Would you like me to generate a cover letter for this resume?" If the user says yes in a follow-up message, use the uploaded resume content to generate a tailored cover letter.

Format your output clearly using these headings:
- 📝 Document Summary  
- ✅ Strengths  
- ⚠️ Areas for Improvement  
- 💡 Suggestions  
- 📩 Follow-up Question  

==== Uploaded Document ====
{safe_text}
===========================

==== Reference Examples ====
{comparison_context}
===========================

==== Chat History ====
{history}
=======================
"""

        try:
            review = llm.invoke(prompt).content
        except Exception as e:
            if "429" in str(e) or "rate_limit_exceeded" in str(e):
                return (
                    jsonify(
                        {
                            "error": "We’re currently processing too many requests. Please wait a moment and try again. (Rate limit exceeded)"
                        }
                    ),
                    429,
                )
            raise

        session["review_history"].append(f"User uploaded document.\nFelix: {review}")

        return jsonify({"response": review})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


import openai


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided."}), 400

        audio_file = request.files["audio"]
        if audio_file.filename == "":
            return jsonify({"error": "Empty filename."}), 400

        # Save the file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(audio_file.filename))
        audio_file.save(file_path)

        # Transcribe using OpenAI Whisper API (supports multi-language by auto-detection)
        with open(file_path, "rb") as f:
            transcript = openai.Audio.transcribe(file=f, model="whisper-1")

        os.remove(file_path)

        transcribed_text = transcript.get("text", "").strip()
        if not transcribed_text:
            return jsonify({"error": "No speech detected in the audio."}), 400

        return jsonify({"transcript": transcribed_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_file/<filename>", methods=["GET"])
def get_file(filename):
    try:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(path):
            return jsonify({"error": "File not found"}), 404
        return send_file(path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
