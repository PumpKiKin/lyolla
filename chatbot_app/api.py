from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
import os
from dotenv import load_dotenv
from .embeddings import build_faiss_index

# .env 로드
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "faiss_index"

def load_vectorstore():
    # ✅ 벡터스토어가 없으면 자동 생성
    if not DB_PATH.exists():
        print("⚠️ FAISS 인덱스가 없어 새로 생성합니다...")
        build_faiss_index()
        
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sbert-nli",
        model_kwargs={"device": "cpu"})
    return FAISS.load_local(str(DB_PATH), embeddings, allow_dangerous_deserialization=True)

def process_question(user_question, history):
    db = load_vectorstore()
    retriever = db.as_retriever(search_kwargs={"k": 5})
    docs = retriever.invoke(user_question)

    # format history
    history_text = "\n".join([f"{h['role']}: {h['content']}" for h in history[-8:]])

    template = """
    너는 사용자의 질문에 친절하고 간결하게 답변하는 서강대학교 로욜라도서관 도우미야.
    아래 컨텍스트와 이전 대화를 참고해서, 필요한 정보만 정리해서 답변해.
    중복된 표현은 피하고, 불확실한 부분은 '제공된 정보로는 알 수 없습니다'라고 답해.

    출력 규칙:
    1. 항상 `### 🔍 상세 설명` 섹션을 출력하되, 제목은 출력하지 말 것.
    2. 만약 상세 설명이 너무 길다면, **그때만** `### ✏️ 핵심 요약` 섹션을 함께 출력. 이때는 제목을 출력할 것.
    (핵심 요약이 필요하지 않으면 섹션 자체를 출력하지 말 것.)
    3. 항상 `### 🔗 관련 링크` 섹션을 출력. 링크는 HTML `<a>` 태그로 작성.

    ---

    이전 대화: {history}

    컨텍스트: {context}

    질문: {question}

    응답:
    """

    prompt = PromptTemplate.from_template(template)
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "question": user_question,
        "context": docs,
        "history": history_text
    })

    return {"answer": response, "sources": [d.metadata.get("source","") for d in docs]}
