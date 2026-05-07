'use client';

/** Deterministic seed-based sparkline — no external data or library needed */
function seedPoints(seed: number, n = 20): number[] {
  let v = 100;
  let s = seed * 9301;
  return Array.from({ length: n }, () => {
    s = (s * 9301 + 49297) % 233280;
    v = v * (1 + ((s / 233280 - 0.5) * 2) * 0.03);
    return v;
  });
}

export default function Sparkline({
  seed,
  color,
  width = 70,
  height = 24,
}: {
  seed: number;
  color: string;
  width?: number;
  height?: number;
}) {
  const values = seedPoints(seed);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - min) / range) * (height - 2) - 1;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ display: 'block', flexShrink: 0 }}
    >
      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
