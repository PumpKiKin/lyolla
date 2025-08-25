document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");

    // ✅ 마크다운 파서 + 보안 라이브러리 사용
    function renderMarkdown(text) {
        return DOMPurify.sanitize(marked.parse(text));
    }

    // ✅ 말풍선 생성 함수
    function addMessage(text, isUser = false) {
        const msg = document.createElement("div");
        msg.classList.add("message", isUser ? "user-message" : "bot-message");

        if (isUser) {
            // 사용자 메시지는 그냥 텍스트
            msg.textContent = text;
        } else {
            // 챗봇 메시지는 마크다운 처리
            msg.innerHTML = renderMarkdown(text);
        }

        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ✅ 폼 전송 이벤트
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

        try {
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

                if (data.sources && data.sources.length > 0) {
                    const links = data.sources.map((s, i) => {
                        return `[출처 ${i + 1}](${s})`; // ✅ 마크다운 링크로 변환
                    }).join(" ");

                    addMessage(`\n---\n**출처:** ${links}`, false);
                }
            } else {
                addMessage("⚠️ 답변을 불러올 수 없습니다.", false);
            }
        } catch (err) {
            chatMessages.removeChild(loading);
            addMessage("⚠️ 오류 발생: " + err.message, false);
        }
    });
});
