from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .api import process_question

import json

def chat_page(request):
    return render(request, "chatbot_app/chat.html")

@csrf_exempt # 발표용은 주석 해제
def chat_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        q = data.get("question", "")

        history = request.session.get("chat_history", [])

        result = process_question(q, history)

        # 세션에 저장
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": result["answer"]})
        request.session["chat_history"] = history

        return JsonResponse({
            "question": q,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "history": history[-10:],  # 최근 10개만 전달
        })

@csrf_exempt
def reset_chat(request):
    """대화 초기화"""
    request.session["chat_history"] = []
    return JsonResponse({"status": "ok"})
