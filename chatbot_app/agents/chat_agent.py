from .base_agent import BaseAgent
from .vector_store_agent import VectorStoreAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from datetime import datetime

class ChatAgent(BaseAgent):
    """대화 관리 + LLM 응답 담당"""

    def __init__(self):
        self.vector_agent = VectorStoreAgent()
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    # ---------------------------
    # 맥락 기반 질의어 재작성
    # ---------------------------
    def make_search_query(self, user_question: str, history: list) -> str:
        last_user_q = ""
        for h in reversed(history):
            if h["role"] == "user" and h["content"] != user_question:
                last_user_q = h["content"]
                break

        if last_user_q:
            return f"{last_user_q} 관련해서 {user_question}"
        else:
            return user_question


    def run(self, user_question: str, history: list):
        # ---------------------------
        # 1. 맥락 기반 검색 질의어 생성
        # ---------------------------
        search_query = self.make_search_query(user_question, history)

        # ---------------------------
        # 2. RAG 검색 실행
        # ---------------------------
        docs = self.vector_agent.run(search_query)

        # ---------------------------
        # 3. 최근 대화 이력 정리
        # ---------------------------
        history_text = "\n".join(
            [f"{h['role']}: {h['content']}" for h in history[-8:]]
        )

        today = datetime.now().strftime("%Y-%m-%d")

        # ---------------------------
        # 4. 프롬프트 구성
        # ---------------------------
        template = """
        오늘은 {today} 입니다.
        다음의 컨텍스트를 활용해서 질문에 답변해줘
        - 질문에 곧바로 핵심 정보로 답변해줘
        - 어투는 친절하게 해줘
        - 가능하면 500자 이내로 답해줘.
        - 설명이 700자 이상이면 마지막에 간단히 요약해줘
        - 참고할 링크가 있으면 알려주고, 출력은 <a> 태그를 사용해줘
        - 순서가 있는 데이터는 줄바꿈으로 정리해줘
        - 대화 시작 시 한 번만 인사하고, 이후 답변에는 인사를 생략해줘
        - 해당 질문만으로 정보를 제공하기가 어려우면 이전 대화를 참고하여 질문을 재구성한 다음에 다시 문서를 찾아보고 답변해줘
        - 이전 대화 맥락을 참고했는데도 답변하기 어려우면 사용자에게 더 자세한 질문을 해달라고 요청해줘
        
        이전 대화: {history}

        컨텍스트: {context}

        질문: {question}

        응답:
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.model | StrOutputParser()

        # ---------------------------
        # 5. 최종 응답 생성
        # ---------------------------
        response = chain.invoke(
            {
                "today": today,
                "question": user_question,
                "context": docs,
                "history": history_text,
            }
        )

        return {
            "answer": response,
            "sources": [d.metadata.get("source", "") for d in docs],
        }