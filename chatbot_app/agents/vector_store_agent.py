from pathlib import Path
import json
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from .base_agent import BaseAgent

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "faiss_index"


class VectorStoreAgent(BaseAgent):
    """FAISS 벡터스토어 기반 검색 + 질문 응답"""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sbert-nli", model_kwargs={"device": "cpu"}
        )
        if not DB_PATH.exists():
            self.build_index()
        self.db = FAISS.load_local(
            str(DB_PATH), self.embeddings, allow_dangerous_deserialization=True
        )

    # -------------------------------
    # JSON → Document 변환
    # -------------------------------
    def _json_to_documents(self, json_files: List[str]) -> List[Document]:
        all_documents = []
        for file_path in json_files:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "notices" in file_path:
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
                    metadata = {
                        "category": item.get("category", ""),
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                    }
                    content = str(item.get("description", ""))
                    all_documents.append(Document(page_content=content, metadata=metadata))
        return all_documents

    # -------------------------------
    # Document → Chunk
    # -------------------------------
    def _chunk_documents(self, documents: List[Document]) -> List[Document]:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        return text_splitter.split_documents(documents)

    # -------------------------------
    # Index 생성
    # -------------------------------
    def build_index(self):
        json_files = [
            str(BASE_DIR / "database" / "detail_data.json"),
            str(BASE_DIR / "database" / "notices.json"),
        ]
        all_documents = self._json_to_documents(json_files)
        smaller_docs = self._chunk_documents(all_documents)
        vector_store = FAISS.from_documents(smaller_docs, embedding=self.embeddings)
        vector_store.save_local(str(DB_PATH))
        print(f"FAISS 인덱스가 {DB_PATH} 에 저장되었습니다.")

    # -------------------------------
    # Agent 실행
    # -------------------------------
    def run(self, query: str, k: int = 5):
        """RAG 검색 결과 반환"""
        retriever = self.db.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)
        return docs