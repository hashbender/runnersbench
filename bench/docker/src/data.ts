import { addDays, format } from "date-fns";

export type Point = { day: string; seconds: number };

export function series(days: number, seed: number): Point[] {
  const start = new Date(2026, 0, 1);
  let value = 30;
  return Array.from({ length: days }, (_, i) => {
    value = Math.max(10, value + Math.sin(i * seed) * 3);
    return { day: format(addDays(start, i), "MMM d"), seconds: Math.round(value * 10) / 10 };
  });
}
