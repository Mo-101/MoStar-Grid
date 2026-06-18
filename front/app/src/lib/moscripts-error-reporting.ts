export type ErrorOptionsType = {
  mechanism?: "manual" | "onerror" | "unhandledrejection" | "react_error_boundary";
  handled?: boolean;
  severity?: "error" | "warning" | "info";
};

type MoScriptsEvents = {
  captureException?: (
    error: unknown,
    context?: Record<string, unknown>,
    options?: ErrorOptionsType,
  ) => void;
};

declare global {
  interface Window {
    __MoScriptsEvents?: MoScriptsEvents;
  }
}

export function reportMoScriptsError(
  error: unknown,
  context: Record<string, unknown> = {},
  options: ErrorOptionsType = {}
) {
  if (typeof window === "undefined") return;

  window.__MoScriptsEvents?.captureException?.(
    error,
    {
      source: "react_error_boundary",
      route: window.location.pathname,
      ...context,
    },
    {
      mechanism: "react_error_boundary",
      handled: false,
      severity: "error",
    },
  );
}