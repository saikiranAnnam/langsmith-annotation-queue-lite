interface NodeProps {
  value: unknown;
  path: string;
  depth: number;
}

function JsonNode({ value, path, depth }: NodeProps) {
  const childPad = { paddingLeft: `${(depth + 1) * 16}px` };

  if (value === null)
    return <span className="text-purple-600">null</span>;

  if (typeof value === "boolean")
    return <span className="text-purple-600">{String(value)}</span>;

  if (typeof value === "number")
    return <span className="text-amber-500">{value}</span>;

  if (typeof value === "string")
    return (
      <span data-path={path} className="text-green-600">
        &quot;{value}&quot;
      </span>
    );

  if (Array.isArray(value)) {
    if (value.length === 0) return <span>{"[]"}</span>;
    return (
      <>
        {"["}
        <div style={childPad}>
          {value.map((item, i) => (
            <div key={i}>
              <JsonNode value={item} path={`${path}.${i}`} depth={depth + 1} />
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
}

export function JsonViewer({ value, path = "" }: JsonViewerProps) {
  return (
    <div className="px-4 pb-4 text-xs font-mono overflow-auto max-h-[40vh] border-t border-gray-100">
      <JsonNode value={value} path={path} depth={0} />
    </div>
  );
}
