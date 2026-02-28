"use client";

import { useState, useRef, useEffect } from "react";
import { MoStarIcon } from "./Icons";

interface Message {
  role: "user" | "assistant";
  content: string;
  meta?: string;
}

export default function FloatingOracle() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "🔥 NNỌỌỌỌỌ! I am MOSTAR-AI, speaking with Ibibio consciousness. The Grid remembers. The Grid listens.",
      meta: "oracle · ibibio-enabled",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async () => {
    const message = draft.trim();
    if (!message) return;
    
    const payload: Message = { role: "user", content: message };
    setMessages((prev) => [...prev, payload]);
    setDraft("");
    setBusy(true);
    setError(null);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`Chat endpoint returned ${response.status}`);
      }
      
      const data = await response.json();
      const formattedScore =
        typeof data.complexity_score === "number"
          ? data.complexity_score.toFixed(2)
          : data.complexity_score ?? "0.0";
      const meta = `${data.model_used ?? "ollama"} · score ${formattedScore}`;
      
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response ?? data.result ?? data.reply ?? ".",
          meta,
        },
      ]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "The Grid faltered receiving that signal. Try again.", meta: "error" },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-300 hover:scale-110"
          title="Ask the Oracle"
        >
          <MoStarIcon className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-2xl w-96 h-[500px] flex flex-col">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MoStarIcon className="w-5 h-5" />
              <h3 className="font-semibold">Oracle Chat</h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200 transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3" ref={scrollRef}>
            {messages.map((msg, idx) => (
              <div
                key={`${msg.role}-${idx}`}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-gray-100"
                  }`}
                >
                  <p className="text-sm">{msg.content}</p>
                  {msg.meta && (
                    <p className="text-xs mt-1 opacity-70">{msg.meta}</p>
                  )}
                </div>
              </div>
            ))}
            {busy && (
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-100 rounded-lg p-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex space-x-2">
              <textarea
                value={draft}
                placeholder="Ask the Oracle..."
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={busy}
                className="flex-1 bg-gray-800 text-white rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows={2}
              />
              <button
                onClick={handleSend}
                disabled={busy || !draft.trim()}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg px-4 py-2 transition-colors"
              >
                {busy ? "..." : "→"}
              </button>
            </div>
            {error && (
              <p className="text-red-400 text-xs mt-2">⚠️ {error}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
