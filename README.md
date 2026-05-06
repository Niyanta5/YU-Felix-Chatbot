# Canvas Chatbot

Canvas Chatbot is an AI-powered Retrieval-Augmented Generation (RAG) assistant built to help Yeshiva University students quickly access academic and Canvas-related support. The system combines document ingestion, semantic search, and LLM-based response generation to answer questions about Canvas navigation, course materials, assignments, FAQs, and student resources through a simple chat interface.

This project focuses on solving a real student workflow problem by connecting scattered academic resources into one accessible AI assistant.

---

## Prerequisites

Before running the project, make sure you have the following installed:

- Python 3.11 or later
- Git
- pip
- Optional: Azure CLI
- Optional: Terraform
- Optional: Azure Functions Core Tools

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository_url>
cd <repository_folder>
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

Activate the environment:

```bash
source venv/bin/activate
```

For Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=<your_openai_key>
CHATBOT_ENV=dev
```

Supported values for `CHATBOT_ENV`:

```text
dev
staging
production
```

For Azure Functions, create a `local.settings.json` file inside the `Data Warehouse/` directory:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<connection_string>",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AUTH_KEY1": "<api_auth_key>",
    "DATABASE_URL": "<postgres_connection_string>"
  }
}
```

---

## Running Locally

### Run the Graduate Chatbot

```bash
export OPENAI_API_KEY=<your_openai_key>
python Web/app_grad.py
```

### Run the Undergraduate Chatbot

```bash
export OPENAI_API_KEY=<your_openai_key>
python Web/app_undergrad.py
```

Then open:

```text
http://127.0.0.1:5000/
```

---

## Build or Update the Knowledge Base

The knowledge base pipeline processes Canvas content, FAQs, documents, and resource pages into vector stores that can be queried by the chatbot.

```bash
cd canvas_knowledgebase
pip install -r requirements.txt
python create_knowledge_base.py
```

After generation, copy or link the updated vector store into the appropriate application directory, such as:

```text
Web/
faq_vectorStore/
graduate_vectorStore/
undergraduate_vectorStore/
```

---

## Generate Knowledge Transfer Documents

The project includes scripts to generate technical and non-technical documentation.

```bash
cd KT
python generate_docs.py
```

This generates:

```text
Technical_Document.docx
NonTechnical_Document.docx
```

---

## Run Azure Functions Locally

```bash
cd "Data Warehouse"
pip install -r requirements.txt
func start
```

This requires Azure Functions Core Tools.

---

## Deployment

### Deploy Flask Web App

The `Web/` folder can be deployed to an Azure Web App or any WSGI-compatible hosting environment.

Recommended production setup:

```bash
gunicorn app_grad:app
```

or

```bash
gunicorn app_undergrad:app
```

Make sure the following environment variables are configured in the Azure App Service settings:

```text
OPENAI_API_KEY
CHATBOT_ENV
```

---

### Deploy Azure Infrastructure with Terraform

```bash
cd "Data Warehouse/terraform"
terraform init
terraform plan -out plan.out
terraform apply plan.out
```

---

### Deploy Azure Function Code

```bash
az functionapp deployment source config-zip \
  --name <FunctionAppName> \
  --resource-group <ResourceGroup> \
  --src ../Batch_trigger.zip
```

Update `<FunctionAppName>` and `<ResourceGroup>` with your Azure resource names.

---

## How It Works

1. Course materials, FAQs, and resource pages are collected from supported sources.
2. Documents are parsed, cleaned, and chunked.
3. Chunks are embedded and stored in ChromaDB vector stores.
4. When a student asks a question, the chatbot retrieves the most relevant context.
5. The LLM generates a grounded response using the retrieved information.
6. The user can provide feedback through thumbs-up/down interactions.

---

## Example Use Cases

Students can ask questions such as:

```text
Where can I find my course syllabus?
How do I submit an assignment on Canvas?
What readings are available for this course?
Where can undergraduate students find career resources?
How do I navigate to course modules?
```

---

## Project Impact

This project demonstrates how RAG-based systems can reduce student friction by turning scattered academic resources into an accessible conversational assistant. It combines AI engineering, backend development, cloud deployment, and user-centered product thinking into one end-to-end application.

---

## Documentation

Knowledge Transfer documentation is available in the `KT/` directory:

- `Technical_Document.md`
- `NonTechnical_Document.md`

Generated Word documents can also be created using:

```bash
python KT/generate_docs.py
```

---

## Contributing

Contributions are welcome. Please open an issue or pull request for improvements, bug fixes, or feature additions.

Recommended contribution steps:

1. Create a feature branch.
2. Make your changes.
3. Test the chatbot locally.
4. Update documentation if needed.
5. Open a pull request.

---

## License

Add your license information here.

Example:

```text
MIT License
```

---

## Author

Built by Niyanta Pandey and the Felix AI team as an AI/RAG application in May 2025 to improve student access to Canvas and academic resources.
