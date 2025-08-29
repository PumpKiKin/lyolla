from pathlib import Path
import json, hashlib, time
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "faiss_index"
INDEX_FILES = ["index.faiss", "index.pkl"]
MANIFEST = DB_PATH / "manifest.json"

class VectorStoreAgent:
    """FAISS 벡터스토어 기반 검색 + 질문 응답 (안전한 인덱스 보장)"""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sbert-nli", model_kwargs={"device": "cpu"}
        )
        self._ensure_index()  # 변경 사항 모두 점검
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
                for item in (data if isinstance(data, list) else [data]):
                    metadata = {
                        "source": item.get("source", ""),
                        "title": item.get("title", ""),
                        "author": item.get("author", ""),
                        "date": item.get("date", ""),
                    }
                    content = f"[제목] {item.get('title','')}\n\n{item.get('content','')}"
                    all_documents.append(Document(page_content=content, metadata=metadata))
            else:
                for item in (data if isinstance(data, list) else [data]):
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
        self._chunk_size = 800
        self._chunk_overlap = 200
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap
        )
        return splitter.split_documents(documents)

    # -------------------------------
    # 매니페스트(원본 해시) 생성/검증
    # -------------------------------
    def _file_hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    def _current_manifest(self, json_files: List[Path]) -> dict:
        return {
            "model_name": getattr(self.embeddings, "model_name", ""),
            "chunk_size": getattr(self, "_chunk_size", 800),
            "chunk_overlap": getattr(self, "_chunk_overlap", 200),
            "files": {str(p): self._file_hash(p) for p in json_files},
        }

    def _manifest_matches(self, cur: dict) -> bool:
        if not MANIFEST.exists():
            return False
        try:
            saved = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            return False
        keys = ["model_name", "chunk_size", "chunk_overlap", "files"]
        return all(saved.get(k) == cur.get(k) for k in keys)

    # -------------------------------
    # Index 생성
    # -------------------------------
    def build_index(self):
        DB_PATH.mkdir(parents=True, exist_ok=True)
        json_files = [
            BASE_DIR / "database" / "detail_data.json",
            BASE_DIR / "database" / "notices.json",
        ]
        all_documents = self._json_to_documents([str(p) for p in json_files])
        smaller_docs = self._chunk_documents(all_documents)
        vector_store = FAISS.from_documents(smaller_docs, embedding=self.embeddings)
        vector_store.save_local(str(DB_PATH))

        # 매니페스트 저장
        cur_manifest = self._current_manifest(json_files)
        MANIFEST.write_text(json.dumps(cur_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f" FAISS 인덱스가 {DB_PATH} 에 저장되었습니다.")

    # -------------------------------
    # Index 보장 (무결성/원본변경/경합 대응)
    # -------------------------------
    def _index_present(self) -> bool:
        if not DB_PATH.exists():
            return False
        for f in INDEX_FILES:
            if not (DB_PATH / f).exists():
                return False
        return True

    def _ensure_index(self):
        DB_PATH.mkdir(parents=True, exist_ok=True)
        
        lock = DB_PATH / ".build.lock"
        json_files = [
            BASE_DIR / "database" / "detail_data.json",
            BASE_DIR / "database" / "notices.json",
        ]
        try:
            # 간단한 락(동시 빌드 방지)
            if lock.exists():
                # 다른 프로세스가 빌드 중일 수 있음 → 잠깐 대기 후 재확인
                time.sleep(1.5)

            if not self._index_present():
                lock.touch(exist_ok=True)
                self.build_index()
            else:
                cur_manifest = self._current_manifest(json_files)
                if not self._manifest_matches(cur_manifest):
                    lock.touch(exist_ok=True)
                    print("원본/설정이 바뀌어 인덱스를 재생성합니다.")
                    self.build_index()
        except Exception as e:
            print(f"인덱스 확인/생성 중 오류 발생: {e}\n→ 재생성 시도")
            try:
                lock.touch(exist_ok=True)
                self.build_index()
            finally:
                if lock.exists():
                    lock.unlink(missing_ok=True)
        finally:
            if lock.exists():
                lock.unlink(missing_ok=True)

    # -------------------------------
    # Agent 실행
    # -------------------------------
    def run(self, query: str, k: int = 5):
        retriever = self.db.as_retriever(search_kwargs={"k": k})
        return retriever.invoke(query)
