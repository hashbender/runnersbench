import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { series } from "./data";

const runners = ["x64", "arm64", "macOS"];

export function App() {
  return (
    <main>
      <h1>Build times</h1>
      {runners.map((name, i) => (
        <section key={name}>
          <h2>{name}</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={series(90, i + 1)}>
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line dataKey="seconds" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </section>
      ))}
    </main>
  );
}
