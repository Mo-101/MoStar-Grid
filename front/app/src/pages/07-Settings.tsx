import { useDashboard } from "@/routes/dashboard";

export default function Settings() {
  const { apiBase } = useDashboard();

  return (
    <section className="main">
      <aside className="panel left p-5 flex flex-col justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[var(--gold)]">SETTINGS</h1>
          <div className="kicker mt-1">COMMAND PARAMETERS</div>
          <p className="text-sm text-foreground/80 mt-4 leading-relaxed">
            Manage connection keys, tokens, and local microservices configurations for the Nairobi-α Command Center.
          </p>
        </div>
      </aside>
      <main className="panel col-span-2 p-5 font-mono text-xs space-y-4">
        <div className="kicker">SYSTEM CONFIGURATION PARAMETERS</div>
        <div className="box m-0">
          <div className="row"><span>CLUSTER ID</span><span>nairobi-alpha</span></div>
          <div className="row"><span>GRID API ADDRESS</span><span>{apiBase}</span></div>
          <div className="row"><span>PIPER TTS ADDRESS</span><span>http://localhost:41071</span></div>
          <div className="row"><span>OLLAMA PROXY</span><span>127.0.0.1:11434</span></div>
        </div>
        <div className="box m-0">
          <h3 className="text-xs text-[var(--gold)] font-bold mb-2">COVENANT THRESHOLDS</h3>
          <div className="row"><span>IKANG (FIRE) THRESHOLD</span><span>0.75</span></div>
          <div className="row"><span>MMỌNG (WATER) THRESHOLD</span><span>0.70</span></div>
          <div className="row"><span>AFIM (AIR) THRESHOLD</span><span>0.65</span></div>
          <div className="row"><span>ISONG (EARTH) THRESHOLD</span><span>0.80</span></div>
        </div>
      </main>
    </section>
  );
}
