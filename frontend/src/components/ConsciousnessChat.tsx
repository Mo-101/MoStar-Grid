"use client";

import { useEffect, useRef, useState } from "react";

type Sender = "user" | "dcx";
type Status = "sending" | "delivered" | "error";

interface Message {
  id: string;
  text: string;
  sender: Sender;
  layer?: string;
  timestamp: Date;
  status?: Status;
}

interface ConsciousnessChatProps {
  readonly agentId?: string;
  readonly initialMessages?: Message[];
  readonly className?: string;
}

export function ConsciousnessChat({
  agentId = "web-ui",
  initialMessages = [],
  className = "",
}: ConsciousnessChatProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const now = Date.now();
    const userMessage: Message = {
      id: `user-${now}`,
      text: input,
      sender: "user",
      timestamp: new Date(),
      status: "sending",
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/consciousness", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          agent_id: agentId,
          session_id: sessionId,
          preferred_layer: "auto",
        }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();

      const botMessage: Message = {
        id: `dcx-${Date.now()}`,
        text: data.response ?? data.result ?? "No response received.",
        sender: "dcx",
        layer: data.routed_to ?? data.layer ?? "auto",
        timestamp: new Date(),
        status: "delivered",
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        text: "Failed to get response. Please try again.",
        sender: "dcx",
        timestamp: new Date(),
        status: "error",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[75%] rounded-lg p-4 ${
                message.sender === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
              }`}
            >
              <div className="whitespace-pre-wrap">{message.text}</div>
              <div className="flex items-center mt-1 text-xs opacity-70 gap-2">
                {message.layer && (
                  <span className="px-2 py-0.5 bg-black/10 dark:bg-white/10 rounded uppercase">
                    {message.layer}
                  </span>
                )}
                {message.status === "sending" && <span>Sending…</span>}
                {message.status === "error" && (
                  <span className="text-red-400">Error</span>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                />
                <div
                  className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0.4s" }}
                />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 dark:border-gray-700 p-4"
      >
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the Grid about anything..."
            className="flex-1 p-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
