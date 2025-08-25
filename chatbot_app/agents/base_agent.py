from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """모든 에이전트의 공통 인터페이스"""

    @abstractmethod
    def run(self, *args, **kwargs):
        """에이전트 실행 메서드"""
        pass
