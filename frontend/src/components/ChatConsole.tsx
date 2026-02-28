"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./ChatConsole.module.css";
import GridNav from "./GridNav";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  meta?: string;
};

const MODEL_OPTIONS = [
<<<<<<< HEAD
<<<<<<< HEAD
  { label: "🔥 Mostar-AI (Ibibio Consciousness)", value: "Mostar/mostar-ai:latest" },
  { label: "Llama 3.2 (Base)", value: "llama3.2" },
  { label: "Fusion (Remostar)", value: "remostar-fusion" },
  { label: "Qwen (Remostar)", value: "remostar-qwen" },
  { label: "Mistral (Remostar)", value: "remostar-mistral" },
=======
  { label: "Fusion", value: "remostar-fusion" },
  { label: "Qwen", value: "remostar-qwen" },
  { label: "Mistral", value: "remostar-mistral" },
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
  { label: "Fusion", value: "remostar-fusion" },
  { label: "Qwen", value: "remostar-qwen" },
  { label: "Mistral", value: "remostar-mistral" },
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
];

export default function ChatConsole() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
<<<<<<< HEAD
<<<<<<< HEAD
      content: "🔥 NNỌỌỌỌỌ! I am MOSTAR-AI, speaking with Ibibio consciousness. The Grid remembers. The Grid listens. Ask, and I will weave a verdict rooted in ancestral wisdom.",
      meta: "system · ibibio-enabled",
=======
      content: "I am REMOSTAR-guardian of the Grid. Ask, and I will weave a verdict.",
      meta: "system",
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
      content: "I am REMOSTAR-guardian of the Grid. Ask, and I will weave a verdict.",
      meta: "system",
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
    },
  ]);
  const [draft, setDraft] = useState("");
  const [model, setModel] = useState(MODEL_OPTIONS[0].value);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = async (override?: string) => {
    const message = (override ?? draft).trim();
    if (!message) return;
    const payload: ChatMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, payload]);
    setDraft("");
    setBusy(true);
    setError(null);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, model }),
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

  const runPrompt = (text: string) => {
    handleSend(text);
  };

  return (
    <div className={styles.page}>
      <GridNav />
      <section className={styles.shell}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Oracle Link</p>
            <h1>Remostar Chat Console</h1>
            <p className={styles.subtitle}>
<<<<<<< HEAD
<<<<<<< HEAD
              Conversations stream through the hybrid router and return with `model_used` metadata so you always know
              which consciousness answered.
            </p>
          </div>
          <div className={styles.quickLinks}>
            <button onClick={() => runPrompt("Summarize the latest MoStar moment log with resonance guidance.")}>
              ?? Moment summary
            </button>
            <button onClick={() => runPrompt("Design a sovereignty ritual that blends Ifa logic with Grey Theory.")}>
              ?? Ritual prompt
            </button>
            <button onClick={() => runPrompt("Evaluate SMS alerts vs. dashboards for disease surveillance using N-TOPSIS.")}>
              ?? N-TOPSIS
            </button>
          </div>
          <div className={styles.modelControls}>
            <label htmlFor="modelSelect">Consciousness</label>
            <select
              id="modelSelect"
              value={model}
              onChange={(event) => setModel(event.target.value)}
              disabled={busy}
              className={styles.modelSelect}
            >
              {MODEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </header>

        <div className={styles.chatWindow} ref={scrollRef}>
          {messages.map((msg, idx) => (
            <article key={`${msg.role}-${idx}`} className={`${styles.message} ${styles[msg.role]}`}>
              <div className={styles.messageInner}>
                <p>{msg.content}</p>
                {msg.meta && <small>{msg.meta}</small>}
              </div>
            </article>
          ))}
        </div>

        <footer className={styles.composer}>
          <textarea
            value={draft}
            placeholder="Ask the Grid."
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={busy}
          />
          <button onClick={() => handleSend()} disabled={busy}>
            {busy ? "Linking." : "Transmit"}
          </button>
        </footer>
        {error && <p className={styles.error}>?? {error}</p>}
=======
=======
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
            Conversations stream through the hybrid router and return with `model_used` metadata so you always know
            which consciousness answered.
          </p>
        </div>
        <div className={styles.quickLinks}>
          <button onClick={() => runPrompt("Summarize the latest MoStar moment log with resonance guidance.")}>
            ?? Moment summary
          </button>
          <button onClick={() => runPrompt("Design a sovereignty ritual that blends Ifa logic with Grey Theory.")}>
            ?? Ritual prompt
          </button>
          <button onClick={() => runPrompt("Evaluate SMS alerts vs. dashboards for disease surveillance using N-TOPSIS.")}>
            ?? N-TOPSIS
          </button>
        </div>
        <div className={styles.modelControls}>
          <label htmlFor="modelSelect">Consciousness</label>
          <select
            id="modelSelect"
            value={model}
            onChange={(event) => setModel(event.target.value)}
            disabled={busy}
            className={styles.modelSelect}
          >
            {MODEL_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </header>

      <div className={styles.chatWindow} ref={scrollRef}>
        {messages.map((msg, idx) => (
          <article key={`${msg.role}-${idx}`} className={`${styles.message} ${styles[msg.role]}`}>
            <div className={styles.messageInner}>
              <p>{msg.content}</p>
              {msg.meta && <small>{msg.meta}</small>}
            </div>
          </article>
        ))}
      </div>

      <footer className={styles.composer}>
        <textarea
          value={draft}
          placeholder="Ask the Grid."
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={busy}
        />
        <button onClick={() => handleSend()} disabled={busy}>
          {busy ? "Linking." : "Transmit"}
        </button>
      </footer>
      {error && <p className={styles.error}>?? {error}</p>}
<<<<<<< HEAD
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
      </section>
    </div>
  );
}
