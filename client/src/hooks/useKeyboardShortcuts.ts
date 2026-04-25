import { useEffect, useRef } from "react";

type Handlers = {
  onScore: (score: number) => void;
  onSubmitActive: () => void;
  onCycleNext: () => void;
  onComplete: () => void;
  onSkip: () => void;
  onToggleLegend: () => void;
};

// Keyboard shortcuts for the annotation workflow.
// Uses a handlers ref so the event listener is only registered once (on mount),
// but always calls the latest handler closures without stale state.
export function useKeyboardShortcuts(handlers: Handlers, disabled = false) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  useEffect(() => {
    if (disabled) return;

    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if ((e.target as HTMLElement).isContentEditable) return;

      const h = handlersRef.current;
      switch (e.key) {
        case "1": h.onScore(0.1); break;
        case "2": h.onScore(0.2); break;
        case "3": h.onScore(0.3); break;
        case "4": h.onScore(0.4); break;
        case "5": h.onScore(0.5); break;
        case "6": h.onScore(0.6); break;
        case "7": h.onScore(0.7); break;
        case "8": h.onScore(0.8); break;
        case "9": h.onScore(0.9); break;
        case "0": h.onScore(1.0); break;
        case "Enter":
          e.preventDefault();
          h.onSubmitActive();
          break;
        case "Tab":
          e.preventDefault();
          h.onCycleNext();
          break;
        case "n":
        case "N":
          h.onComplete();
          break;
        case "s":
        case "S":
          h.onSkip();
          break;
        case "?":
          h.onToggleLegend();
          break;
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [disabled]);
}
