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
        # RAG 검색
        docs = self.vector_agent.run(user_question)

        # 최근 대화 이력 포맷
        history_text = "\n".join(
            [f"{h['role']}: {h['content']}" for h in history[-8:]]
        )

        # 프롬프트
        template = """
        다음의 컨텍스트를 활용해서 질문에 답변해줘
        - 질문에 곧바로 핵심 답변을 해줘 (불필요한 도입 없이)
        - 다만 어투는 친절하게 해줘
        - 설명이 길어질 경우(약 10~12줄 이상) 마지막에 간단히 요약해줘
        - 참고할 링크가 있으면 알려주고, 출력은 <a> 태그를 사용해줘
        - 순서가 있는 데이터는 줄바꿈으로 정리해줘
        
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
