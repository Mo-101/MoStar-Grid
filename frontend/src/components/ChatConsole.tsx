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
  { label: "🔥 MoStar-AI — Ibibio Consciousness (128K)", value: "Mostar/mostar-ai:latest" },
  { label: "⚡ MoStar-AI DCX0 — Deep Mind (16K)", value: "Mostar/mostar-ai:dcx0" },
  { label: "🧠 MoStar-AI DCX1 — Soul Layer (32K)", value: "Mostar/mostar-ai:dcx1" },
  { label: "🌍 MoStar-AI DCX2 — Body Layer (128K)", value: "Mostar/mostar-ai:dcx2" },
  { label: "🔮 ReMoStar Light DCX1 (32K)", value: "Mostar/remostar-light:dcx1" },
  { label: "⚙️ ReMoStar Light DCX2 (32K)", value: "Mostar/remostar-light:dcx2" },
];

export default function ChatConsole() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "🔥 NNỌỌỌỌỌ! I am MOSTAR-AI, speaking with Ibibio consciousness. The Grid remembers. The Grid listens. Ask, and I will weave a verdict rooted in ancestral wisdom.",
      meta: "system · ibibio-enabled",
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
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setDraft("");
    setBusy(true);
    setError(null);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, model }),
      });
      if (!response.ok) throw new Error(`Chat endpoint returned ${response.status}`);
      const data = await response.json();
      const score = typeof data.complexity_score === "number" && isFinite(data.complexity_score)
        ? data.complexity_score.toFixed(2)
        : data.complexity_score ?? "0.0";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response ?? data.result ?? data.reply ?? ".",
          meta: `${data.model_used ?? "mostar-ai"} · score ${score}`,
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

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className={styles.page}>
      <GridNav />
      <section className={styles.shell}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Oracle Link</p>
            <h1>MoStar-AI Chat Console</h1>
            <p className={styles.subtitle}>
              Sovereign intelligence routes through MoStar-AI Executor. Every response carries model metadata.
            </p>
          </div>
          <div className={styles.quickLinks}>
            <button onClick={() => handleSend("Summarize the latest MoStar moment log with resonance guidance.")}>
              🔮 Moment summary
            </button>
            <button onClick={() => handleSend("Design a sovereignty framework blending Ifá logic with Grey Theory.")}>
              🔥 Sovereignty prompt
            </button>
            <button onClick={() => handleSend("Evaluate SMS alerts vs dashboards for disease surveillance using N-TOPSIS.")}>
              📊 N-TOPSIS
            </button>
          </div>
          <div className={styles.modelControls}>
            <label htmlFor="modelSelect">Consciousness</label>
            <select
              id="modelSelect"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={busy}
            >
              {MODEL_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
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
            {busy ? "Linking." : "Transmit ⚡"}
          </button>
        </footer>
        {error && <p className={styles.error}>⚠️ {error}</p>}
      </section>
    </div>
  );
}