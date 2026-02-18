import { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [messages, setMessage] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);
  const messagesRef = useRef(null);

  useEffect(()=> {
    if (loading) return;

    const container = messagesRef.current;
    if (container) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [loading]);

  const sendMessage = async () => {
    if (input.trim() === "") return;

    const userMessage = {
      text: input,
      sender: "user"
    }

    setMessage(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: userMessage.text })
      });
      if (!response.ok) {
        const errorData = await response.json();
        setMessage(prev => [...prev, { text: errorData.response || "Error occured.", sender: "bot" }])
        setLoading(false);
        return;
      }

      const data = await response.json();

      const botMessage = {
        text: data.response,
        sender: "bot"
      };

      setMessage(prev => [...prev, botMessage]);

    } catch (error) {
      setMessage(prev => [...prev, { text: "Error connecting to the server.", sender: "bot"}]);
    }

    setLoading(false);
  }

  return (
    <div className="page">
      <div className="header">
        <h1 className="title">Brazilian Jiu-Jitsu Knowledge Assistant</h1>
        <p className="subtitle">
          Ask questions about Brazilian Jiu-Jitsu techniques and concepts.
Responses are generated using a strict Retrieval-Augmented Generation (RAG) pipeline that relies only on curated source material.
        </p>
        <div className="badge">Strict Context Mode Enabled</div>
      </div>

      <div className="chat-container">
        <div className="chat-header">
          <div className="version-tag">v1.0 — Public Release</div>
        </div>

        <div className="messages" ref={messagesRef}>
          {messages.length === 0 && (
            <div className="empty-state">
              Start by asking a question about Brazilian Jiu-Jitsu.
            </div>
          )}
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message-wrapper ${message.sender}`}
              >
                <span
                  className={`bubble bubble-${message.sender}`}
                >
                  {message.text}
                </span>
              </div>
            ))}

            {loading && <p className="loading">Thinking...</p>}

            <div ref={chatEndRef}/>
        </div>

        <div className="input-area">
          <input 
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
            placeholder="Ask a question..."
            className="input" 
          />

          <button onClick={sendMessage} className="button">
            Send
          </button>

        </div>
        
      </div>

      <div className="footer">Built with React, FastAPI, and OpenAI Embeddings.</div>
    </div>
  );
}

export default App;