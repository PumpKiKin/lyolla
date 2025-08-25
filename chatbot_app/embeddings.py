from pathlib import Path
import json
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "faiss_index"

def json_to_documents(json_files: List[str]) -> List[Document]:
    all_documents = []

    for file_path in json_files:
        file = Path(file_path)
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "notices" in file.name:
            for item in data if isinstance(data, list) else [data]:
                metadata = {
                    "source": item.get("source", ""),
                    "title": item.get("title", ""),
                    "author": item.get("author", ""),
                    "date": item.get("date", ""),
                }
                content = f"[제목] {item.get('title','')}\n\n{item.get('content','')}"
                all_documents.append(Document(page_content=content, metadata=metadata))

        else:
            for item in data if isinstance(data, list) else [data]:
                content = str(item.get("description", ""))
                metadata = {
                    "category": item.get("category", ""),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                }
                all_documents.append(Document(page_content=content, metadata=metadata))

    return all_documents

def chunk_documents(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    return text_splitter.split_documents(documents)

def save_to_vector_store(documents: List[Document]) -> None:
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sbert-nli",
        model_kwargs={"device": "cpu"})
    vector_store = FAISS.from_documents(documents, embedding=embeddings)
    vector_store.save_local(str(DB_PATH))

def build_faiss_index():
    """JSON 파일을 읽어서 벡터스토어 생성"""
    json_files = [
        str(BASE_DIR / "database" / "detail_data.json"),
        str(BASE_DIR / "database" / "notices.json"),
    ]
    all_documents = json_to_documents(json_files)
    smaller_documents = chunk_documents(all_documents)
    save_to_vector_store(smaller_documents)
    print(f"✅ FAISS 인덱스가 {DB_PATH} 에 저장되었습니다.")
