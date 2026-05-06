# Non-Technical Knowledge Transfer Document

## 1. Purpose
This document provides end-user guidance for graduate students on using the Canvas Chatbot applications to access course materials, FAQs, and academic resources. It is intended for quick onboarding and training in classroom or support settings.

## 2. Audience
- Graduate students
- Course instructors and teaching assistants
- Academic support staff

## 3. What is the Canvas Chatbot?
The Canvas Chatbot is an interactive assistant accessible via a web page. It understands natural language queries and returns:
- Direct answers to common questions
- Links to course documents (syllabi, assignments, readings)
- Resources from pre-built FAQs and knowledge bases

## 4. Getting Started
1. Open your browser and navigate to the Chatbot URL (e.g., http://127.0.0.1:5000/).
2. Enter your question in plain English (e.g., “How do I submit my assignment?”).
3. Review the response and click any provided links to view or download documents.
4. Ask follow-up questions without repeating context (e.g., “What about the grading rubric?”).

## 5. Key Features
- Natural language Q&A: Type questions as you would ask a tutor.
- Instant document retrieval: Links to files such as syllabi, slides, and FAQs.
- Contextual follow-ups: Continue the conversation without retyping previous details.
- Feedback buttons: Thumbs-up or thumbs-down after each reply to improve quality.

## 6. Graduate vs. Undergraduate Chatbots
| Aspect               | Graduate Chatbot            | Undergraduate Chatbot             |
|----------------------|-----------------------------|-----------------------------------|
| Resource Sources     | FAQs + Canvas course files  | FAQs + Canvas + Career KB         |
| Career Knowledge     | n/a                         | Includes scraped career resources |
| Course Level         | Graduate-level courses      | Undergraduate-level courses       |

## 7. Using the Chatbot in Class Projects
1. Launch the Chatbot interface during lectures or assignments.
2. Encourage students to ask about:
   - Assignment instructions
   - Grading criteria
   - Course schedules and deadlines
   - Resource links (readings, examples)
3. Review feedback to refine your syllabus and FAQs for future classes.

## 8. Feedback and Support
- Use the thumbs-up/down icons to rate each response.
- Provide comments when prompted to highlight inaccuracies or missing information.
- Contact the support team (listed below) for unresolved questions or improvement requests.

## 9. Transferring to the Next Class
When a new semester or course section begins:
1. Update source materials (Canvas content and FAQ CSVs) with current semester data.
2. Ask the technical team to regenerate the knowledge base:
   ```bash
   cd KT && python generate_docs.py  # updates KT documents (.docx)
   cd canvas_knowledgebase && python create_knowledge_base.py  # rebuilds vectorstores
   ```
3. Redeploy the Chatbot application with refreshed data.

## 10. Contacts
- **Infrastructure & Maintenance**
  - Shashank, Dheeraj, Chaitanya (Development)
  - JK, Niyanta, Bhavitha (Azure Deployment)