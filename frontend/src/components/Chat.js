import React from "react";


// Format LLM message (text + code blocks)
function formatMessage(text) {

  if (!text) return null;

  const blocks = text.split("```");

  return blocks.map((block, index) => {

    // Code block
    if (index % 2 === 1) {

      return (
        <pre key={index} className="code-block">
          <code>{block.trim()}</code>
        </pre>
      );
    }

    // Normal text
    return block
      .split("\n")
      .filter(line => line.trim() !== "")
      .map((line, i) => (

        <p key={`${index}-${i}`} className="chat-text">
          {line}
        </p>

      ));
  });
}


function Chat({
  messages,
  question,
  setQuestion,
  sendQuestion,
  goBack
}) {

  return (

    <div className="chat-card slide-up">


      {/* HEADER */}
      <div className="chat-header">

        <button
          className="back-btn"
          onClick={goBack}
        >
          Back
        </button>

        <h2>Repo Doc Bot</h2>

      </div>


      {/* CHAT BOX */}
      <div className="chat-box">

        {messages.map((msg, i) => (

          <div
            key={i}
            className={
              msg.sender === "user"
                ? "chat user"
                : "chat bot"
            }
          >

            {msg.sender === "bot"
              ? formatMessage(msg.text)
              : msg.text
            }

          </div>

        ))}

      </div>


      {/* INPUT */}
      <div className="chat-input">

        <input
          className="input"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask about repository..."
          onKeyDown={e => {
            if (e.key === "Enter") sendQuestion();
          }}
        />

        <button
          className="btn primary"
          onClick={sendQuestion}
        >
          Send
        </button>

      </div>

    </div>
  );
}

export default Chat;
