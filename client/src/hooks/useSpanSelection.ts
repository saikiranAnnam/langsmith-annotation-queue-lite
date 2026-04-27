import { useState, useRef } from "react";
import type { Feedback, FeedbackSpan } from "../types";

export function useSpanSelection(highlights: Feedback[] = []) {
  const [pendingSpan, setPendingSpan] = useState<FeedbackSpan | null>(null);
  const [pendingText, setPendingText] = useState<string | null>(null);
  const [overlapWarning, setOverlapWarning] = useState(false);
  const [crossFieldWarning, setCrossFieldWarning] = useState(false);
  const crossFieldTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseUp = (_e: React.MouseEvent) => {
    try {
      const selection = window.getSelection();

      if (!selection || selection.isCollapsed || selection.rangeCount === 0) {
        setPendingSpan(null);
        setPendingText(null);
        setOverlapWarning(false);
        return;
      }

      const range = selection.getRangeAt(0);

      // commonAncestorContainer is the deepest DOM node that contains both the
      // start and end of the selection. If the reviewer dragged within a single field
      // it will be that field's span (or a node inside it). If they dragged across
      // multiple fields it will be a higher-level ancestor with no data-path.
      const ancestor = range.commonAncestorContainer;
      const el =
        ancestor.nodeType === Node.ELEMENT_NODE
          ? (ancestor as Element).closest("[data-path]")
          : (ancestor as Text).parentElement?.closest("[data-path]");

      if (!el) {
        // Span crosses a JSON field boundary — show inline guidance, auto-clear after 3s.
        setPendingSpan(null);
        setPendingText(null);
        setOverlapWarning(false);
        setCrossFieldWarning(true);
        if (crossFieldTimer.current) clearTimeout(crossFieldTimer.current);
        crossFieldTimer.current = setTimeout(() => setCrossFieldWarning(false), 3000);
        return;
      }
      setCrossFieldWarning(false);

      // Measure how many characters come before the selection start within this field.
      // Cloning the range and trimming it to [fieldStart, selectionStart] then calling
      // toString() handles any number of nested text nodes (e.g. existing <mark> splits).
      const preRange = range.cloneRange();
      preRange.selectNodeContents(el);
      preRange.setEnd(range.startContainer, range.startOffset);
      const start = preRange.toString().length;

      const selectedText = range.toString();
      const end = start + selectedText.length;

      if (start === end) {
        setPendingSpan(null);
        setPendingText(null);
        setOverlapWarning(false);
        return;
      }

      const path = el.getAttribute("data-path")!.split(".");
      const pathStr = path.join(".");
      const overlaps = highlights.some(
        (f) =>
          f.span_path?.join(".") === pathStr &&
          f.span_start_index != null &&
          f.span_end_index != null &&
          start < f.span_end_index! &&
          end > f.span_start_index!
      );

      setPendingSpan({ span_path: path, span_start_index: start, span_end_index: end });
      setPendingText(selectedText);
      setOverlapWarning(overlaps);
    } catch {
      // DOM APIs can throw on detached/invalid nodes — discard the selection silently
      setPendingSpan(null);
      setPendingText(null);
      setOverlapWarning(false);
    }
  };

  const clearSpan = () => {
    setPendingSpan(null);
    setPendingText(null);
    setOverlapWarning(false);
    setCrossFieldWarning(false);
  };

  return { pendingSpan, pendingText, overlapWarning, crossFieldWarning, clearSpan, handleMouseUp };
}
