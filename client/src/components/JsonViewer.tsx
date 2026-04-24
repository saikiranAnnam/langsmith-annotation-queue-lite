import { useState } from "react";
import type { Feedback } from "../types";
import { HighlightTooltip } from "./HighlightTooltip";
import { getRubricColor } from "../lib/rubricColors";

interface NodeProps {
  value: unknown;
  path: string;
  depth: number;
  highlights: Feedback[];
  onHighlightHover: (feedback: Feedback, rect: DOMRect) => void;
  onHighlightLeave: () => void;
}

function JsonNode({
  value,
  path,
  depth,
  highlights,
  onHighlightHover,
  onHighlightLeave,
}: NodeProps) {
  const childPad = { paddingLeft: `${(depth + 1) * 16}px` };

  if (value === null) return <span className="text-purple-600">null</span>;

  if (typeof value === "boolean")
    return <span className="text-purple-600">{String(value)}</span>;

  if (typeof value === "number")
    return <span className="text-amber-500">{value}</span>;

  if (typeof value === "string") {
    // All feedbacks with a span on this path, sorted left-to-right.
    const hits = highlights
      .filter(
        (f) =>
          f.span_path?.join(".") === path &&
          f.span_start_index != null &&
          f.span_end_index != null
      )
      .sort((a, b) => (a.span_start_index ?? 0) - (b.span_start_index ?? 0));

    let inner: React.ReactNode = value;
    if (hits.length > 0) {
      const segments: React.ReactNode[] = [];
      let cursor = 0;
      for (const h of hits) {
        const start = h.span_start_index!;
        const end = h.span_end_index!;
        if (start < cursor) continue; // skip overlapping spans
        if (start > cursor) segments.push(value.slice(cursor, start));
        segments.push(
          <mark
            key={h.id}
            data-feedback-id={h.id}
            className={`${getRubricColor(h.key).mark} cursor-help rounded not-italic`}
            onMouseEnter={(e) =>
              onHighlightHover(h, (e.currentTarget as Element).getBoundingClientRect())
            }
            onMouseLeave={onHighlightLeave}
          >
            {value.slice(start, end)}
          </mark>
        );
        cursor = end;
      }
      if (cursor < value.length) segments.push(value.slice(cursor));
      inner = <>{segments}</>;
    }

    // The opening/closing quotes live outside the data-path span so that
    // selection offsets inside the span map directly to character positions
    // in the string value (no +/-1 adjustment needed in useSpanSelection).
    return (
      <>
        <span className="text-green-600">&quot;</span>
        <span data-path={path} className="text-green-600">
          {inner}
        </span>
        <span className="text-green-600">&quot;</span>
      </>
    );
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <span>{"[]"}</span>;
    return (
      <>
        {"["}
        <div style={childPad}>
          {value.map((item, i) => (
            <div key={i}>
              <JsonNode
                value={item}
                path={`${path}.${i}`}
                depth={depth + 1}
                highlights={highlights}
                onHighlightHover={onHighlightHover}
                onHighlightLeave={onHighlightLeave}
              />
              {i < value.length - 1 && ","}
            </div>
          ))}
        </div>
        {"]"}
      </>
    );
  }

  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    if (entries.length === 0) return <span>{"{}"}</span>;
    return (
      <>
        {"{"}
        <div style={childPad}>
          {entries.map(([key, val], i) => (
            <div key={key}>
              <span className="text-blue-600 font-semibold">&quot;{key}&quot;</span>
              {": "}
              <JsonNode
                value={val}
                path={path ? `${path}.${key}` : key}
                depth={depth + 1}
                highlights={highlights}
                onHighlightHover={onHighlightHover}
                onHighlightLeave={onHighlightLeave}
              />
              {i < entries.length - 1 && ","}
            </div>
          ))}
        </div>
        {"}"}
      </>
    );
  }

  return <span>{String(value)}</span>;
}

export interface JsonViewerProps {
  value: unknown;
  /** Dot-notation prefix for data-path attributes, e.g. "inputs" or "outputs" */
  path?: string;
  /** Feedbacks that have span data — their spans are rendered as amber highlights */
  highlights?: Feedback[];
}

export function JsonViewer({ value, path = "", highlights = [] }: JsonViewerProps) {
  // When the user hovers a highlighted mark we store the feedback + element
  // rect here so we can position the tooltip right above the mark.
  const [tooltip, setTooltip] = useState<{ feedback: Feedback; rect: DOMRect } | null>(null);

  return (
    <div className="relative px-4 pb-4 text-xs font-mono overflow-auto max-h-[40vh] border-t border-gray-100">
      <JsonNode
        value={value}
        path={path}
        depth={0}
        highlights={highlights}
        onHighlightHover={(feedback, rect) => setTooltip({ feedback, rect })}
        onHighlightLeave={() => setTooltip(null)}
      />
      {tooltip && (
        <HighlightTooltip feedback={tooltip.feedback} anchorRect={tooltip.rect} />
      )}
    </div>
  );
}
