from .base_agent import BaseAgent
from .vector_store_agent import VectorStoreAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser


class ChatAgent(BaseAgent):
    """대화 관리 + LLM 응답 담당"""

    def __init__(self):
        self.vector_agent = VectorStoreAgent()
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    def run(self, user_question: str, history: list):
        # 🔍 RAG 검색
        docs = self.vector_agent.run(user_question)

        # 📜 최근 대화 이력 포맷
        history_text = "\n".join(
            [f"{h['role']}: {h['content']}" for h in history[-8:]]
        )

        # 🎯 프롬프트
        template = """
        너는 서강대학교 로욜라 도서관 도우미야.
        아래 컨텍스트와 이전 대화를 참고해서, 필요한 정보만 답변해.
        불확실하면 "제공된 정보로는 알 수 없습니다."라고 답해.

        출력 규칙:
        1. 항상 `### 🔍 상세 설명` 섹션 출력 (제목은 생략).
        2. 답변이 너무 길면 `### ✏️ 핵심 요약`도 출력.
        3. 항상 `### 🔗 관련 링크` 섹션 출력 (HTML `<a>` 태그).

        ---
        이전 대화: {history}

        컨텍스트: {context}

        질문: {question}

        응답:
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.model | StrOutputParser()

        response = chain.invoke(
            {"question": user_question, "context": docs, "history": history_text}
        )

        return {
            "answer": response,
            "sources": [d.metadata.get("source", "") for d in docs],
        }
