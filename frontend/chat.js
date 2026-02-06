const chatBox = document.getElementById("chat-box");
const questionInput = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");
const chatSpinner = document.getElementById("chat-spinner");

function addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);

    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.addEventListener("click", sendQuestion);
questionInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendQuestion();
});

async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;

    addMessage(question, "user");
    questionInput.value = "";

    sendBtn.disabled = true;
    chatSpinner.classList.remove("hidden");

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });

        if (!response.ok) throw new Error();
        const data = await response.json();
        addMessage(data.answer, "bot");

    } catch {
        addMessage("Error getting response from server.", "bot");
    } finally {
        chatSpinner.classList.add("hidden");
        sendBtn.disabled = false;
    }
}
