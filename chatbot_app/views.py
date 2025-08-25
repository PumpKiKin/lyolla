from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .api import process_question
import json

def chat_page(request):
    return render(request, "chatbot_app/chat.html")


def chat_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        q = data.get("question", "")

        # 세션에서 히스토리 불러오기 (없으면 초기화)
        history = request.session.get("chat_history", [])

        # 백엔드에서 LLM 호출
        result = process_question(q, history)

        # 히스토리에 추가
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": result["answer"]})
        request.session["chat_history"] = history  # 세션 저장

        return JsonResponse({
            "question": q,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "history": history[-10:],  # 최근 10개만 프론트로
        })

@csrf_exempt
def reset_chat(request):
    if request.method == "POST":
        request.session["chat_history"] = []  # 세션 비우기
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)