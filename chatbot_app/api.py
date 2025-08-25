from .agents.chat_agent import ChatAgent

chat_agent = ChatAgent()

def process_question(user_question, history):
    return chat_agent.run(user_question, history)
