import type { ReactNode } from "react";

type TierColor = "orange" | "red" | "zinc";

interface TierTabProps {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  title: string;
  subtitle: string;
  color: TierColor;
}

const colorMap: Record<TierColor, { active: string; idle: string }> = {
  orange: {
    active: "border-tier-orange bg-tier-orange/10 text-tier-orange shadow-glow-orange",
    idle: "border-border hover:border-tier-orange/50 hover:text-tier-orange/70",
  },
  red: {
    active: "border-tier-red bg-tier-red/10 text-tier-red shadow-glow-red",
    idle: "border-border hover:border-tier-red/50 hover:text-tier-red/70",
  },
  zinc: {
    active: "border-tier-zinc bg-tier-zinc/10 text-tier-zinc",
    idle: "border-border hover:border-muted-foreground hover:text-muted-foreground",
  },
};

const TierTab = ({ active, onClick, icon, title, subtitle, color }: TierTabProps) => {
  const c = colorMap[color];
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 flex flex-col items-center gap-3 p-4 sm:p-6 border-2 rounded-2xl transition-smooth ${
        active ? c.active : c.idle
      }`}
    >
      <span className={`transition-smooth ${active ? "scale-110" : "scale-100 opacity-60"}`}>
        {icon}
      </span>
      <div className="text-center">
        <p className="font-black text-xs sm:text-sm uppercase tracking-wider">{title}</p>
        <p className="text-[10px] uppercase tracking-tighter opacity-60 mt-1">{subtitle}</p>
      </div>
    </button>
  );
};

export default TierTab;
