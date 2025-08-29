document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");
    const resetBtn = document.getElementById("reset-chat");
    const resetNotification = document.getElementById("reset-notification");

    // 마크다운 파서 + 보안 라이브러리 사용
    function renderMarkdown(text) {
        return DOMPurify.sanitize(marked.parse(text));
    }

    // 말풍선 생성 함수
    function addMessage(text, isUser = false) {
        const msg = document.createElement("div");
        msg.classList.add("message", isUser ? "user-message" : "bot-message");

        if (isUser) {
            // 사용자 메시지는 그냥 텍스트
            msg.textContent = text;
        } else {
            // 챗봇 메시지는 마크다운 처리
            msg.innerHTML = renderMarkdown(text);

            // 모든 링크를 새 탭에서 열리도록 강제
            msg.querySelectorAll("a").forEach(link => {
                link.setAttribute("target", "_blank");
                link.setAttribute("rel", "noopener noreferrer");
            });
        }

        chatMessages.appendChild(msg);
        // chatMessages.scrollTop = chatMessages.scrollHeight;
        chatMessages.scrollTop = msg.offsetTop - 80;
    }

    // 대화 초기화 버튼
    resetBtn.addEventListener("click", async () => {
        chatMessages.innerHTML = "";  // 화면 비우기
        
        try {
            await fetch("/chat/reset/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                }
            });

            // 알림 메시지 표시
            resetNotification.classList.add("show");

            // 1초 후에 알림 메시지 숨기기
            setTimeout(() => {
                resetNotification.classList.remove("show");
            }, 1000);

        } catch (err) {
            console.error("Reset error:", err);
            // 오류 발생 시 다른 방식으로 알림을 표시할 수 있습니다.
        }
    });

    // 폼 전송 이벤트
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // 사용자 메시지 추가
        addMessage(text, true);
        userInput.value = "";

        // 로딩 메시지
        const loading = document.createElement("div");
        loading.classList.add("message", "bot-message");
        loading.innerHTML = `
        <div class="loading-dots">
            <span></span><span></span><span></span>
        </div>
        `;
        chatMessages.appendChild(loading);
        chatMessages.scrollTop = chatMessages.scrollHeight; 

        try {
            // const response = await fetch("http://127.0.0.1:8000/chat/api/", { // 개발용
            const response = await fetch("/chat/api/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: JSON.stringify({ question: text }),
            });

            const data = await response.json();
            chatMessages.removeChild(loading);

            if (data.answer) {
                addMessage(data.answer, false);
            } else {
                addMessage("답변을 불러올 수 없습니다.", false);
            }
        } catch (err) {
            chatMessages.removeChild(loading);
            addMessage("오류 발생: " + err.message, false);
        }
    });
});
