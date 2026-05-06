# Technical Knowledge Transfer Document

## 1. Overview
This document provides a comprehensive technical walkthrough of the Canvas Chatbot project, covering both the web applications (Flask-based Graduate and Undergraduate chatbots) and the Data Warehouse components (Azure Functions and Terraform infrastructure). It is intended for developers and DevOps engineers responsible for maintaining, extending, or deploying the system.

## 2. Repository Structure
```plaintext
/
├── Web/                      # Flask web applications
│   ├── app_grad.py           # Graduate chatbot entrypoint
│   ├── app_undergrad.py      # Undergraduate chatbot entrypoint
│   ├── templates/            # HTML templates
│   ├── static/               # CSS, JS, and image assets
│   └── faq_scrape_vectorStore/ # Scraped KB for undergraduates
├── canvas_knowledgebase/     # Canvas API scraping and processing scripts
├── Canvas_Grad_chromadb_store/ # Pre-built Canvas graduate vectorstore data
├── Data Warehouse/           # Azure Functions code and Terraform IaC
│   ├── Architecture Diagram.png
│   ├── Batch_trigger/        # Batch ingestion Function app
│   ├── daily_trigger_api/    # Daily trigger Function app
│   ├── helper/               # Utility modules (DB, email, logging)
│   ├── pgsql/                # SQL query definitions
│   ├── terraform/            # Terraform modules and configs
│   ├── requirements.txt      # Dependencies for Functions
│   └── host.json             # Azure Functions host configuration
├── faq_vectorStore/          # FAQ vectorstore data
├── graduate_vectorStore/     # Graduate Canvas vectorstore
├── undergraduate_vectorStore/ # Undergraduate Canvas vectorstore
├── KT/                       # Documentation and KT scripts
│   ├── Technical_Document.md
│   └── NonTechnical_Document.md
└── requirements.txt          # Project-wide Python dependencies
``` 

## 3. Dependencies
All Python dependencies are declared in `requirements.txt` (project root) and `Data Warehouse/requirements.txt` (Functions). Key libraries:
  - Flask, flask-session, flask-cors
  - OpenAI SDK (`langchain-openai`, `tiktoken`)
  - ChromaDB client (`chromadb`)
  - Web scraping: `beautifulsoup4`, `requests`
  - Document parsing: `PyMuPDF`, `python-docx`
  - Data processing: `pandas`
  - Configuration: `python-dotenv`
  - Azure Functions: `azure-functions`, `psycopg2-binary`

## 4. Environment & Configuration
### 4.1 Local Setup
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the sample environment file or create `.env` in project root:
   ```ini
   OPENAI_API_KEY=<your_openai_key>
   CHATBOT_ENV=dev      # dev | staging | production
   ```

### 4.2 Azure Functions (Data Warehouse)
1. Navigate to `Data Warehouse` folder:
   ```bash
   cd "Data Warehouse"
   ```
2. Install function dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Provide function settings via `local.settings.json` or environment variables:
   - `AUTH_KEY1` (for API calls)
   - Database connection strings (PostgreSQL)

## 5. Web Applications (Flask)
This section describes the architecture and code for the Graduate and Undergraduate chatbot services.

### 5.1 Architecture
Both chatbots expose a web UI and a JSON API to handle:
  - User input and chat history
  - Semantic retrieval from vectorstores (ChromaDB)
  - Language model calls (OpenAI GPT)
  - File/link serving and feedback

**Entry Points**:
  - `app_grad.py` for graduate students
  - `app_undergrad.py` for undergraduates

### 5.2 Vectorstores & Data Sources
  - **FAQ Store**: Preprocessed FAQs from Azure Blob Storage, persisted in `faq_vectorStore/`.
  - **Canvas Store**: Course materials fetched via Canvas API; stored under `graduate_vectorStore/` or `undergraduate_vectorStore/`.
  - **Scraped KB**: (Undergraduate only) scraped from career services site and stored in `Web/faq_scrape_vectorStore/`.

### 5.3 Code Structure
```plaintext
- app_<level>.py            # Flask app, routes and main logic
- utils.py (if present)     # Shared helper functions
- templates/                # Jinja2 HTML templates (chat UI)
- static/                   # CSS, JS, images
``` 

Key helper functions:
- `normalize_question()`, `truncate_text_to_tokens()`
- `format_docs()`, `generate_prompt()`
- `cached_llm_response()` to memoize LLM calls

### 5.4 Running & Debugging
```bash
# Graduate chatbot
export OPENAI_API_KEY=<key>
python Web/app_grad.py

# Undergraduate chatbot
python Web/app_undergrad.py

# Access UI: http://127.0.0.1:5000/
```

### 5.5 Production Deployment (Azure Web App)
- Package code into ZIP and deploy via Azure CLI or GitHub Actions
- Configure App Settings for environment variables
- Use Gunicorn or built-in hosting for performance

### 5.1 Vectorstore Initialization
Each app script (`app_grad.py`, `app_undergrad.py`) initializes:
```python
Chroma(
  persist_directory=<STORE_DIR>,
  embedding_function=OpenAIEmbeddings()
)
```
Retrievers are created via `.as_retriever()` for semantic search.

## 6. Data Warehouse (Azure Functions & Terraform)
The Data Warehouse component automates ingestion, processing, and storage of student and counseling data.

### 6.1 Architecture Overview
- Refer to `Data Warehouse/Architecture Diagram.png` for high-level flow.
- Core services:
  1. **Batch_trigger**: HTTP-triggered function for bulk data ingestion
  2. **daily_trigger_api**: HTTP-triggered function for daily updates and notifications
  3. **PostgreSQL**: Relational database for structured data
  4. **Email service**: Sends error and completion notifications

### 6.2 Azure Functions Code
Location: `Data Warehouse/Batch_trigger` and `Data Warehouse/daily_trigger_api`
- Triggers defined in `function.json` (HTTP triggers)
- Business logic delegates to helper modules in `Data Warehouse/helper/`

Helper modules:
- `api.py`: Fetch external data via HTTP
- `insert_db.py`: Batch insertion into PostgreSQL with conflict handling
- `errorEmail.py`, `sendEmail.py`: Notification utilities
- `postgres.py`: Connection management

### 6.3 Database Queries
Stored SQL in `Data Warehouse/pgsql/query.sql`.

### 6.4 Infrastructure as Code (Terraform)
Root directory: `Data Warehouse/terraform`
- **Modules**: `function_app`, `postgresql_flexible_server`, `storage_account`, `key_vault`, etc.
- **Configuration files**: `main.tf`, `variables.tf`, `provider.tf`, `backend.tf`, `output.tf`

**Deployment commands**:
```bash
cd "Data Warehouse/terraform"
terraform init
terraform plan -out plan.out
terraform apply plan.out
```

After provisioning, deploy Function code:
```bash
az functionapp deployment source config-zip \
  --name <FunctionAppName> \
  --resource-group <ResourceGroup> \
  --src ../Batch_trigger.zip
```

### 6.2 app_undergrad.py (Undergraduate)
- Similar structure with extra KB retriever.
- Vectorstores:
  - FAQ (`faq_vectorStore`)
  - KB (`Web/faq_scrape_vectorStore`)
  - Canvas (`undergraduate_vectorStore`)
- Key helpers: `format_docs`, `normalize_question`, `generate_prompt`, etc.

## 7. Knowledge Base Generation
Canvas content and FAQs are ingested and vectorized separately.
- **Canvas scraping**: Scripts in `canvas_knowledgebase/` fetch course pages and attachments.
- **Markdown-to-Docx**: `KT/generate_docs.py` converts KT markdown to `.docx` for stakeholder distribution.

## 8. Prompt Engineering & LLM Integration
System prompts enforce tone, context limits, and link handling.
Example flow in `generate_prompt()` and `cached_llm_response()`.

## 9. API Endpoints Summary
| Route               | Method | Description                         |
|---------------------|--------|-------------------------------------|
| `/`                 | GET    | Serves chat UI (`index.html`)       |
| `/chat`             | POST   | Handles Q&A requests                |
| `/get_file/{name}`  | GET    | Downloads uploaded or course files  |
| `/feedback`         | POST   | Captures user feedback              |

## 10. Troubleshooting & Monitoring
- Check Flask logs for stack traces.
- Verify vectorstore directories and file permissions.
- Monitor Azure Functions execution in the Portal.

## 11. Next Steps & Roadmap
- Automate vectorstore rebuilds on source updates.
- Add OAuth2 authentication for Canvas API and users.
- Instrument metrics (latency, usage) via Azure Application Insights.

## 12. Contacts
- Development: Shashank, Dheeraj, Chaitanya
- Azure & DevOps: JK, Niyanta, Bhavitha

## 8. Prompt Engineering
- System instructions embed brand voice (“Felix”) and boundaries.
- Previous conversation and contextual snippets are concatenated.
- Final prompt assembled with:
  ```python
  prompt = generate_prompt(context, question, chat_history)
  response = cached_llm_response(prompt)
  ```

## 9. API Endpoints
- `/`: Renders `index.html`.
- `/chat` [POST]: Accepts JSON `{message, history}`; returns `{response, links}`.
- `/get_file/<filename>` [GET]: Serves files from `uploads/`.
- `/feedback` [POST]: Stores feedback in session.

## 10. File Uploads & Serving
- Uploaded user files saved under `uploads/`.
- Accessible via `/get_file/<filename>` endpoint.

## 11. Running Locally
```bash
export OPENAI_API_KEY=<key>
# For grad chatbot
python Web/app_grad.py
# For undergrad chatbot
python Web/app_undergrad.py
```  
Open http://127.0.0.1:5000/ in browser.

## 12. Deployment Considerations
- Use Gunicorn or Azure Web App for production.
- Ensure environment variables are securely stored.
- Persist vectorstore directories on disk or Azure Files.

## 13. Troubleshooting
- Check Flask server logs for exceptions.
- Verify vectorstore directories exist and contain embeddings.
- Confirm valid `OPENAI_API_KEY` and network access.

## 14. Next Steps
- Automate vectorstore rebuild on data updates.
- Add authentication (e.g., OAuth2 for Canvas API).
- Monitor usage metrics and latency.