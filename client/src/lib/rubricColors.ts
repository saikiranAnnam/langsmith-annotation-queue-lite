type ColorTokens = { dot: string; badge: string; mark: string; markText: string };

// Palette of visually distinct Tailwind color stops. Each entry follows the
// same structural pattern (dot=400, badge=50/700/100, mark=200, markText=900)
// so the styling stays consistent regardless of which slot a key lands on.
const PALETTE: ColorTokens[] = [
  { dot: "bg-purple-400",  badge: "bg-purple-50  text-purple-700  border-purple-100",  mark: "bg-purple-200",  markText: "text-purple-900"  },
  { dot: "bg-blue-400",    badge: "bg-blue-50    text-blue-700    border-blue-100",    mark: "bg-blue-200",    markText: "text-blue-900"    },
  { dot: "bg-amber-400",   badge: "bg-amber-50   text-amber-700   border-amber-100",   mark: "bg-amber-200",   markText: "text-amber-900"   },
  { dot: "bg-emerald-400", badge: "bg-emerald-50 text-emerald-700 border-emerald-100", mark: "bg-emerald-200", markText: "text-emerald-900" },
  { dot: "bg-rose-400",    badge: "bg-rose-50    text-rose-700    border-rose-100",    mark: "bg-rose-200",    markText: "text-rose-900"    },
  { dot: "bg-cyan-400",    badge: "bg-cyan-50    text-cyan-700    border-cyan-100",    mark: "bg-cyan-200",    markText: "text-cyan-900"    },
  { dot: "bg-orange-400",  badge: "bg-orange-50  text-orange-700  border-orange-100",  mark: "bg-orange-200",  markText: "text-orange-900"  },
  { dot: "bg-indigo-400",  badge: "bg-indigo-50  text-indigo-700  border-indigo-100",  mark: "bg-indigo-200",  markText: "text-indigo-900"  },
  { dot: "bg-pink-400",    badge: "bg-pink-50    text-pink-700    border-pink-100",    mark: "bg-pink-200",    markText: "text-pink-900"    },
  { dot: "bg-teal-400",    badge: "bg-teal-50    text-teal-700    border-teal-100",    mark: "bg-teal-200",    markText: "text-teal-900"    },
];

// Cache so the same key always maps to the same color within a session.
const cache = new Map<string, ColorTokens>();

function hashKey(key: string): number {
  let h = 0;
  for (let i = 0; i < key.length; i++) {
    h = (Math.imul(31, h) + key.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

export function getRubricColor(key: string): ColorTokens {
  const k = key.toLowerCase();
  if (!cache.has(k)) {
    cache.set(k, PALETTE[hashKey(k) % PALETTE.length]);
  }
  return cache.get(k)!;
}
