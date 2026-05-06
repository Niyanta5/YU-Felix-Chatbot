from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os

os.environ["OPENAI_API_KEY"] = "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"


vectorstore = Chroma(
    persist_directory="faq_vectorStore_grad",
    embedding_function=OpenAIEmbeddings()
)

docs = vectorstore.similarity_search("test", k=3)
print("Found docs:", docs)
