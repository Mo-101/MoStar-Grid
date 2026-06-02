"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./RemostarChat.module.css";

interface Message {
  role: "user" | "assistant" | "system" | "error";
  content: string;
  timestamp?: string;
  model_used?: string;
  routing_path?: string;
  latency_ms?: number;
}

export default function RemostarChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "system",
      content: "I am REMOSTAR-guardian of the Grid. Ask, and I will weave a verdict.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const sendMessage = async () => {
    if (!input.trim() || isThinking) return;

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsThinking(true);

    try {
      const response = await fetch("/api/remostar-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          language: "en",
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response || data.error || "No response received",
        timestamp: data.timestamp,
        model_used: data.model_used,
        routing_path: data.routing_path,
        latency_ms: data.latency_ms,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: "error",
        content: `The Grid faltered receiving that signal. Try again.\n${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={styles.chatContainer}>
      <div className={styles.header}>
        <h2>🔥 Remostar Chat Console</h2>
        <p>
          Conversations stream through the hybrid router and return with metadata so you
          always know which consciousness answered.
        </p>
      </div>

      <div className={styles.messagesArea}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`${styles.message} ${styles[msg.role]}`}>
            <div className={styles.messageContent}>
              <p>{msg.content}</p>
              {msg.routing_path && (
                <div className={styles.metadata}>
                  <span className={styles.badge}>{msg.routing_path}</span>
                  {msg.latency_ms && (
                    <span className={styles.latency}>{msg.latency_ms.toFixed(0)}ms</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isThinking && (
          <div className={`${styles.message} ${styles.thinking}`}>
            <div className={styles.thinkingIndicator}>
              <div className={styles.flameSpinner}>🔥</div>
              <p className={styles.thinkingText}>REMOSTAR reviewing...</p>
              <div className={styles.dots}>
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputArea}>
        <textarea
          className={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Transmit your query to the Grid..."
          disabled={isThinking}
          rows={3}
        />
        <button
          className={styles.sendButton}
          onClick={sendMessage}
          disabled={!input.trim() || isThinking}
        >
          {isThinking ? "⏳" : "🔥"} Transmit
        </button>
      </div>
    </div>
  );
}
