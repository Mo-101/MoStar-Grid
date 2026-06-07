import { useNavigate } from "@tanstack/react-router";

type RollCallState = "idle" | "awakening" | "ready";

interface Props {
  state: RollCallState;
  onBegin: () => void | Promise<void>;
}

export function EnterGridButton({ state, onBegin }: Props) {
  const navigate = useNavigate();

  const label =
    state === "idle"
      ? "BEGIN GRID BOOT"
      : state === "awakening"
        ? "AWAKENING ..."
        : "ENTER GRID ->";

  const handleClick = () => {
    if (state === "idle") {
      void onBegin();
      return;
    }

    if (state === "ready") {
      navigate({ to: "/dashboard" });
    }
  };

  const isActive = state !== "awakening";

  return (
    <button
      onClick={handleClick}
      disabled={state === "awakening"}
      className="px-8 py-3 font-mono text-sm tracking-widest transition-all duration-500"
      style={
        isActive
          ? {
              border: "1px solid #f6c453",
              color: "#f6c453",
              boxShadow: "0 0 24px rgba(246,196,83,0.35)",
              cursor: "pointer",
            }
          : {
              border: "1px solid rgba(255,255,255,0.12)",
              color: "rgba(255,255,255,0.28)",
              cursor: "wait",
            }
      }
    >
      {label}
    </button>
  );
}
