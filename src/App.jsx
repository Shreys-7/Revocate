
import { useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([
    {
      role: "assistant",
      text: "Hello! I am REVOCATE, your Indian law assistant. Ask me about legal sections, terms, or scenarios, and I'll find relevant information from the provided legal documents."
    }
  ]);
  const [loading, setLoading] = useState(false);

  async function sendMessage(e) {
    e.preventDefault();

    const question = message.trim();
    if (!question || loading) return;

    setChat((previous) => [
      ...previous,
      { role: "user", text: question }
    ]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/chat/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          
        body: JSON.stringify({
          message: question,
          history: chat.slice(-12).map((item) => ({
            role: item.role,
            content: item.text
          }))
        })

        }
      );

      const responseText = await response.text();
      let data;

      try {
        data = JSON.parse(responseText);
      } catch {
        throw new Error(
          `Invalid server response (HTTP ${response.status}). Check Django.`
        );
      }

      if (!response.ok) {
        throw new Error(
          data.error ||
          data.detail ||
          `Server error: HTTP ${response.status}`
        );
      }

      if (!data.answer) {
        throw new Error("The server did not return an answer.");
      }

      setChat((previous) => [
        ...previous,
        {
          role: "assistant",
          text: data.answer,
          sources: Array.isArray(data.sources)
            ? data.sources
            : []
        }
      ]);
    } catch (error) {
      console.error("REVOCATE API error:", error);

      setChat((previous) => [
        ...previous,
        {
          role: "assistant",
          text: `Sorry, something went wrong: ${error.message}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">⚖</div>
          <div>
            <h1>REVOCATE</h1>
            <p>AI Legal Assistant</p>
          </div>
        </div>

        <nav>
          <a href="#about">About</a>
          <a href="#sections">Legal Sections</a>
        </nav>
      </header>

      <main className="layout">
        <section className="chat-panel">
          <div className="chat-messages" aria-live="polite">
            {chat.map((item, index) => (
              <div
                className={`message ${
                  item.role === "user"
                    ? "user-message"
                    : "assistant-message"
                }`}
                key={index}
              >
                <strong>
                  {item.role === "user" ? "You" : "REVOCATE"}
                </strong>

                <p>{item.text}</p>

                {item.sources?.length > 0 && (
                  <details>
                    <summary>View retrieved legal context</summary>

                    {item.sources.map((source, i) => (
                      <p className="source" key={i}>
                        {typeof source === "string"
                          ? source
                          : source.text ||
                            JSON.stringify(source)}
                      </p>
                    ))}
                  </details>
                )}
              </div>
            ))}

            {loading && (
              <div className="message assistant-message">
                <strong>REVOCATE</strong>
                <p className="loading-text">
                  Searching legal documents...
                </p>
              </div>
            )}
          </div>

          <form className="input-area" onSubmit={sendMessage}>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask about Indian law or a legal section..."
              aria-label="Your legal question"
              disabled={loading}
            />

            <button
              type="submit"
              disabled={loading || !message.trim()}
            >
              {loading ? "Wait..." : "➤ Send"}
            </button>
          </form>
        </section>

        <aside className="sidebar">
          <section className="info-box" id="about">
            <div className="section-heading">
              <span className="heading-icon">i</span>
              <h3>How it works</h3>
            </div>

            <ol className="steps">
              <li>Enter your legal question below.</li>
              <li>
                REVOCATE retrieves relevant passages using ChromaDB.
              </li>
              <li>
                AI generates an answer using the retrieved context.
              </li>
              <li>
                Verify the information against the original legal documents.
              </li>
            </ol>
          </section>

          <section className="info-box" id="sections">
            <div className="section-heading">
              <span className="heading-icon">▤</span>
              <h3>Source Data</h3>
            </div>

            <p className="source-description">
              Legal documents indexed in the REVOCATE knowledge base.
            </p>

            <div className="tech-list">
              <div className="tech-item">
                <span className="tech-icon">▤</span>
                <div>
                  <strong>Backend</strong>
                  <p>Django REST API</p>
                </div>
              </div>

              <div className="tech-item">
                <span className="tech-icon">◉</span>
                <div>
                  <strong>Retrieval</strong>
                  <p>ChromaDB</p>
                </div>
              </div>

              <div className="tech-item">
                <span className="tech-icon">⚛</span>
                <div>
                  <strong>Frontend</strong>
                  <p>React</p>
                </div>
              </div>
            </div>
          </section>
        </aside>
      </main>

      <footer>
        REVOCATE provides AI-assisted legal information, not a substitute
        for advice from a qualified lawyer.
      </footer>
    </div>
  );
}

export default App;
