import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Glyph } from "@/components/grid/glyph";

export type NavKey =
  | "overview"
  | "council"
  | "sanctuary"
  | "watchtower"
  | "mindgraph"
  | "moscripts"
  | "settings";

export const NAV_ITEMS: { key: NavKey; label: string; to: string }[] = [
  { key: "overview", label: "OVERVIEW", to: "/dashboard" },
  { key: "council", label: "COUNCIL", to: "/dashboard/council" },
  { key: "sanctuary", label: "SANCTUARY", to: "/dashboard/sanctuary" },
  { key: "watchtower", label: "WATCHTOWER", to: "/dashboard/watchtower" },
  { key: "mindgraph", label: "MIND GRAPH", to: "/dashboard/mind-graph" },
  { key: "moscripts", label: "MOSCRIPTS", to: "/dashboard/moscripts" },
  { key: "settings", label: "SETTINGS", to: "/dashboard/settings" },
];

function clock() {
  return new Date().toLocaleTimeString("en-GB", { hour12: false });
}

export function useGridClock() {
  const [time, setTime] = useState(clock());
  useEffect(() => {
    const t = window.setInterval(() => setTime(clock()), 1000);
    return () => window.clearInterval(t);
  }, []);
  return time;
}

export function TopBar({ active, status = "AWAKENED" }: { active: NavKey; status?: string }) {
  const time = useGridClock();

  return (
    <header className="gc-top">
      <div className="gc-brand">
        <div className="gc-crest">
          <Glyph name="covenant" size={26} glow="var(--gold)" />
        </div>
        <div>
          MOSTAR GRID
          <small>EXECUTOR OF THE COVENANT</small>
        </div>
      </div>

      <nav className="gc-nav">
        {NAV_ITEMS.map((item) => (
          <Link key={item.key} to={item.to} className={item.key === active ? "on" : ""}>
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="gc-status">
        GRID STATUS — {status}
        <span>{time} UTC</span>
      </div>
    </header>
  );
}

export function FooterBar() {
  return (
    <footer className="gc-foot">
      <span>◆ MOSTAR COVENANT</span>
      <span>HONOR FIRST · STRIKE FAST · SEE AHEAD · STAY UNTOUCHABLE</span>
      <span>QSEAL:MO_SOULPRINT_V1</span>
    </footer>
  );
}

export const chromeCss = `
.gc-top {
  display: grid;
  grid-template-columns: 285px minmax(0, 1fr) 270px;
  align-items: center;
  border-bottom: 1px solid rgba(0,216,255,.12);
  height: 64px;
}
.gc-brand {
  display: flex;
  gap: 12px;
  align-items: center;
  color: var(--gold);
  letter-spacing: .3em;
  font-size: 16px;
  font-weight: 800;
}
.gc-brand small {
  display: block;
  font-size: 8px;
  letter-spacing: .16em;
  color: #d0a843;
  font-weight: 400;
}
.gc-crest {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border: 1px solid var(--gold);
  box-shadow: 0 0 20px #f6c45366;
  background: #f6c45322;
  border-radius: 50%;
}
.gc-nav {
  height: 46px;
  margin: auto;
  display: flex;
  border: 1px solid rgba(0,216,255,.18);
  background: rgba(0,0,0,.38);
  clip-path: polygon(3% 0,97% 0,100% 50%,97% 100%,3% 100%,0 50%);
  overflow: hidden;
}
.gc-nav a {
  padding: 14px 18px;
  border-right: 1px solid rgba(0,216,255,.16);
  font-size: 10px;
  letter-spacing: .16em;
  color: #b8c5d8;
  white-space: nowrap;
  text-decoration: none;
}
.gc-nav a:last-child { border-right: none; }
.gc-nav a.on {
  color: var(--gold);
  background: linear-gradient(180deg,#f6c4531f,transparent);
  box-shadow: inset 0 -2px var(--gold);
}
.gc-status {
  text-align: right;
  color: var(--green);
  letter-spacing: .2em;
  font-size: 10px;
}
.gc-status span {
  display: block;
  color: white;
  letter-spacing: .1em;
  margin-top: 4px;
}
.gc-foot {
  display: flex;
  justify-content: space-between;
  color: #7b8492;
  letter-spacing: .2em;
  font-size: 10px;
  align-items: center;
}
@media (max-width: 1200px) {
  .gc-top { grid-template-columns: 1fr; height: auto; row-gap: 8px; padding: 8px 0; }
  .gc-nav { overflow: auto; width: 100%; margin: 0; }
  .gc-status { text-align: left; }
}
`;
