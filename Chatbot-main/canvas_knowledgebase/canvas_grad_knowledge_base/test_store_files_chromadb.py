import os
import pytest # type: ignore
from pathlib import Path
from langchain.schema import Document # type: ignore

# Import the helper function from your module.
# Adjust the import statement as necessary.
from canvas_knowledgebase.canvas_grad_knowledge_base.store_files_grad_chromadb import load_documents_from_dirs

@pytest.fixture
def temp_dir_with_files(tmp_path):
    """
    Fixture that creates a temporary directory with a text file, a PDF, and a DOCX file.
    We'll simulate PDF and DOCX file loading using monkeypatching.
    """
    dir_path = tmp_path / "canvas_downloads"
    dir_path.mkdir()
    
    # Create a dummy text file
    text_file = dir_path / "dummy.txt"
    text_file.write_text("Dummy text content", encoding="utf-8")
    
    # Create a dummy PDF file (its content is irrelevant because we will override the loader)
    pdf_file = dir_path / "dummy.pdf"
    pdf_file.write_text("irrelevant", encoding="utf-8")
    
    # Create a dummy DOCX file (its content is irrelevant because we will override the loader)
    docx_file = dir_path / "dummy.docx"
    docx_file.write_text("irrelevant", encoding="utf-8")
    
    return str(dir_path)

def test_load_documents_text_file(tmp_path):
    # Test that a simple text file is loaded properly.
    dir_path = tmp_path / "canvas_downloads"
    dir_path.mkdir()
    text_file = dir_path / "dummy.txt"
    text_file.write_text("Dummy text content", encoding="utf-8")
    
    docs = load_documents_from_dirs([str(dir_path)])
    assert len(docs) == 1
    assert "Dummy text content" in docs[0].page_content

def test_load_documents_empty_file(tmp_path):
    # Test that an empty file does not produce a document.
    dir_path = tmp_path / "canvas_downloads"
    dir_path.mkdir()
    empty_file = dir_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    
    docs = load_documents_from_dirs([str(dir_path)])
    assert len(docs) == 0

def dummy_loader_factory(dummy_text):
    """
    Returns a dummy loader class that always returns a Document with dummy_text.
    """
    class DummyLoader:
        def __init__(self, file_path):
            self.file_path = file_path
        def load(self):
            return [Document(page_content=dummy_text, metadata={"source": os.path.basename(self.file_path)})]
    return DummyLoader

def test_load_documents_pdf_file(tmp_path, monkeypatch):
    # Test that a PDF file is loaded using the dummy loader.
    dir_path = tmp_path / "canvas_downloads"
    dir_path.mkdir()
    pdf_file = dir_path / "dummy.pdf"
    pdf_file.write_text("irrelevant", encoding="utf-8")
    
    # Monkey-patch PyPDFLoader to return a dummy document.
    dummy_pdf_text = "PDF dummy content"
    monkeypatch.setattr("langchain_community.document_loaders.PyPDFLoader", dummy_loader_factory(dummy_pdf_text))
    
    docs = load_documents_from_dirs([str(dir_path)])
    # Ensure that the PDF file was processed
    assert len(docs) == 1
    assert dummy_pdf_text in docs[0].page_content

def test_load_documents_docx_file(tmp_path, monkeypatch):
    # Test that a DOCX file is loaded using the dummy loader.
    dir_path = tmp_path / "canvas_downloads"
    dir_path.mkdir()
    docx_file = dir_path / "dummy.docx"
    docx_file.write_text("irrelevant", encoding="utf-8")
    
    # Monkey-patch Docx2txtLoader to return a dummy document.
    dummy_docx_text = "DOCX dummy content"
    monkeypatch.setattr("langchain_community.document_loaders.Docx2txtLoader", dummy_loader_factory(dummy_docx_text))
    
    docs = load_documents_from_dirs([str(dir_path)])
    # Ensure that the DOCX file was processed
    assert len(docs) == 1
    assert dummy_docx_text in docs[0].page_content
