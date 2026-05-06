import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import xml.etree.ElementTree as ET
from langchain.text_splitter import CharacterTextSplitter
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import StringIO
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv
import os

def scrape(url):    
    try:
        # Make a request to the URL
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content of the page
        page_content = soup.get_text()
        return page_content

    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}")


# Function to clean and optimize text
def clean_text(text):
    # Remove extra spaces, newlines, and tabs
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    text = text.strip()  # Remove leading/trailing whitespace
    return text



sitemap_url = 'https://www.yu.edu/sitemap.xml'
response = requests.get(sitemap_url)
response.raise_for_status()  # Raise an error for bad responses

root = ET.fromstring(response.content)

url_pattern = r"sgc"

urls = [loc.text for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
filtered_urls = [url for url in urls if re.search(url_pattern, url)]

filtered_urls.append("https://www.yu.edu/sgc/alumni")
filtered_urls.append("https://www.yu.edu/sgc/employers")

chunks_list_web = []
for url in filtered_urls:
    raw_content = scrape(url)
    if raw_content:
        # Clean the raw content
        cleaned_content = clean_text(raw_content)

        # Split the content into chunks for vector embedding
        text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_text(cleaned_content)

        # Store chunks in the list
        chunks_list_web.extend(chunks)

    time.sleep(2)  # Add delay between requests to avoid overloading the server

# Load environment variables
from dotenv import load_dotenv
env_name = os.getenv("CHATBOT_ENV", "dev")  # default to dev if not set
env_path = f"config/{env_name}.env"
load_dotenv(dotenv_path=env_path)
# Azure Storage account credentials

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = "faqs" 
blob_name = "SGC Chatbot Suggestions(FAQs).csv" 

# Initialize the Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)


try:
    blob_data = blob_client.download_blob().content_as_text(encoding="ISO-8859-1")
    df = pd.read_csv(StringIO(blob_data),usecols=['Question', 'Answer'])
except Exception as e:
    print(f"Error reading file from Blob Storage: {e}")
    
faq_df = df.dropna()


chunks_list_faq = []
# Convert FAQ dataframe to formatted text
faq_text = "\n\n".join([f"Q: {row['Question']}\nA: {row['Answer']}" for _, row in faq_df.iterrows()])

# Clean the raw content
faq_cleaned_content = clean_text(faq_text)

# Split the content into chunks for vector embedding
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_text(faq_cleaned_content)

chunks_list_faq.extend(chunks)



# Define a header for the FAQ section
faq_header = "\n\n--- FAQ Section Start ---\n\n"

# Combine the web chunks into a single text
web_content = "\n\n".join(chunks_list_web)

# Combine the FAQ chunks into a single text with the FAQ header
faq_content = faq_header + "\n\n".join(chunks_list_faq)



scraped_doc = Document(page_content=web_content, metadata={"section": "Scraped Content"})
faq_doc = Document(page_content=faq_content, metadata={"section": "FAQ"})


# Split each section separately and retain metadata
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
scraped_splits = text_splitter.split_documents([scraped_doc])
faq_splits = text_splitter.split_documents([faq_doc])

# Combine all splits
all_splits = scraped_splits + faq_splits

# Create vector store with metadata
vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings(), persist_directory="faq_scrape_vectorStore3")

