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

    def run(self, user_question: str, history: list):
        # RAG 검색
        docs = self.vector_agent.run(user_question)

        # 최근 대화 이력 포맷
        history_text = "\n".join(
            [f"{h['role']}: {h['content']}" for h in history[-8:]]
        )

        today = datetime.now().strftime("%Y-%m-%d")

        # 프롬프트
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
        - 해당 질문만으로 답변하기가 어려운 경우에는 자세한 질문을 요청해줘
        
        이전 대화: {history}

        컨텍스트: {context}

        질문: {question}

        응답:
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.model | StrOutputParser()

        response = chain.invoke(
            {"today": today, "question": user_question, "context": docs, "history": history_text}
        )

        return {
            "answer": response,
            "sources": [d.metadata.get("source", "") for d in docs],
        }
