import { useState, useRef, useEffect } from "react";
import "./App.css";
import Footer from "./Footer";

function App() {
  const [messages, setMessage] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showChangelog, setShowChangelog] = useState(false);

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
    if (input.trim() === "" && !input.trim()) return;

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
        <h1 className="title">Brazilian Jiu-Jitsu Knowledge Assistant 🥋</h1>
        <p className="subtitle">
          Ask questions about Brazilian Jiu-Jitsu techniques and concepts.<br/>---<br/>
          <span>Powered by a LangChain agent implementing Retrieval-Augmented Generation (RAG), 
this system dynamically queries a vector database and answers strictly from curated source material.</span>
        </p>
        <div className="badge agent">LangChain Agent</div>
        <div className="badge">Strict Context Mode Enabled</div>
        <div className="badge secure">Protected Mode</div>
      </div>

      <div className="chat-container">
        <div className="chat-header">
          <div className="version-tag">v1.4.0 — Security Enhancements</div>
          <span 
            className="changelog-link"
            onClick={() => {setShowChangelog(true)}}
          > View Changes
          </span>
        </div>

        <div className="messages" ref={messagesRef}>
          {messages.length === 0 && (
            <div className="empty-state">
              Start by asking a question about Brazilian Jiu-Jitsu. For example: “What is Jiu-Jitsu?”
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
              if (e.key === "Enter" && input.trim() && !loading) sendMessage();
            }}
            placeholder="Ask a question..."
            className="input" 
          />

          <button onClick={sendMessage} className="button" aria-label="Send message" title="Send" disabled={!input.trim() || loading}>
            <svg
              className="sendIcon"
              viewBox="0 0 24 24"
              width="20"
              height="20"
              aria-hidden="true"
              focusable="false"
            >
              <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
            </svg>
          </button>

        </div>

        {showChangelog && (
          <div className="modal-overlay" onClick={()=> setShowChangelog(false)}>
            <div className="modal changelogBody" onClick={(e)=> e.stopPropagation()}>
              
              <h3>CHANGELOG</h3>
              <p className="micro-note">
                Pipeline Evolution: Manual Retrieval → Persistent Embeddings → Vector DB → Agent-Orchestrated RAG
              </p>

              <h4>v.1.4.0 - Security Hardening and Testing</h4>
              <ul>
                <li>Enhanced input filtering for prompt injection and special character attacks</li>
                <li>Improved prompt separation with clear instruction/data boundaries</li>
                <li>Added chunk trust scoring to filter poisoned context (0-1 scale)</li>
                <li>Implemented 23 automated security test cases across 8 attack categories</li>
              </ul>

              <h4>v1.3.0 - Agentic RAG Integration</h4>
              <ul>
                <li>Replaced direct LLM calls with a LangChain tool-calling agent</li>
                <li>Encapsulated vector retrieval as a structured RAG tool</li>
                <li>Maintained strict grounding: factual claims require retrieved context</li>
                <li>Improved conversational handling for non-knowledge queries</li>
                <li>UI/UX Improvements (icon button, mobile fixes, scroll modal)</li>
              </ul>

              <h4>v1.2.0 – Vector Database Integration </h4>
                <ul>
                  <li>Replaced manual cosine retrieval with ChromaDB query</li>
                  <li>Added Chroma persistent client + collection (local persistence; Render resets on restart)</li>
                </ul>
              <h4>v1.1.0 – Persistent Embeddings </h4>
                <ul>
                  <li>Added file-based embedding persistence</li>
                  <li>Embeddings now load instantly on server restart</li>
                  <li>Reduced unnecessary OpenAI embedding calls</li>
                </ul>
              <h4>v1.0.1 – UI Improvements</h4>
                <ul>
                  <li>Added in-app changelog modal</li>
                  <li>Added repository CHANGELOG.md</li>
                  <li>Minor UI refinements</li>
                </ul>
              <h4>v.1.0.0 - Initial Release</h4>
              <ul>
                <li>Strict RAG pipeline</li>
                <li>Manual top-3 retrieval</li>
                <li>Rate limiting adn input validation</li>
                <li>Uses a curated knowledge base</li>
                <li>Production deployment</li>
              </ul>

            </div>

          </div>
        )}
        
      </div>

      <div className="sub-text">Built with React, FastAPI, LangChain Agents, ChromaDB, and OpenAI embeddings.</div>
      <Footer />
    </div>
  );
}

export default App;