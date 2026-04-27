type Props = {
  value: string;
  onChange: (val: string) => void;
};

export function RubricScoreInput({ value, onChange }: Props) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-gray-600">Score</label>
        <span className="text-xs text-gray-400">Min: 0 · Max: 1</span>
      </div>
      <input
        type="number"
        min="0"
        max="1"
        step="0.1"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Enter score"
        className="w-full h-10 border border-gray-200 rounded-lg px-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );
}
