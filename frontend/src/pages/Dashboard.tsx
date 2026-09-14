import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";
import { api, DashboardSummary, SpeedEvent, AnalysisSession } from "../lib/api";
import KpiCard from "../components/KpiCard";

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [events, setEvents] = useState<SpeedEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [speedLimit, setSpeedLimit] = useState(60);
  const [pxPerMeter, setPxPerMeter] = useState(8);
  const [file, setFile] = useState<File | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, e] = await Promise.all([api.summary(), api.events()]);
      setSummary(s);
      setEvents(e);
    } catch {
      // handled by apiOnline check below
    }
  }, []);

  useEffect(() => {
    api
      .health()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
    refresh();
  }, [refresh]);

  const runDemo = async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await api.runDemo(speedLimit, pxPerMeter);
      setSession(s);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const runUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const s = await api.analyzeVideo(file, speedLimit, pxPerMeter, false);
      setSession(s);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const chartData = events
    .slice(0, 20)
    .reverse()
    .map((e) => ({ name: `#${e.vehicle_track_id}`, speed: e.estimated_speed_kmh, speeding: e.is_speeding }));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-brand-500" />
          SafeSpeed AI
        </Link>
        <div className="flex items-center gap-2 text-xs">
          <span className={`inline-block h-2 w-2 rounded-full ${apiOnline ? "bg-brand-500" : "bg-alert-500"}`} />
          {apiOnline === null ? "Checking API..." : apiOnline ? "Backend online" : "Backend offline"}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {!apiOnline && apiOnline !== null && (
          <div className="rounded-lg border border-alert-500/40 bg-alert-500/10 p-4 text-sm">
            Can't reach the backend at <code>/api</code>. Start it with{" "}
            <code>uvicorn app.main:app --reload</code> in <code>backend/</code>, then refresh.
          </div>
        )}

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="font-semibold mb-4">Analyze traffic footage</h2>
          <div className="grid sm:grid-cols-2 gap-4 mb-4">
            <label className="text-sm">
              Speed limit (km/h)
              <input
                type="number"
                value={speedLimit}
                onChange={(e) => setSpeedLimit(Number(e.target.value))}
                className="mt-1 w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2"
              />
            </label>
            <label className="text-sm">
              Calibration (pixels per meter)
              <input
                type="number"
                value={pxPerMeter}
                onChange={(e) => setPxPerMeter(Number(e.target.value))}
                className="mt-1 w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2"
              />
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-200"
            />
            <button
              disabled={!file || loading}
              onClick={runUpload}
              className="rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed transition px-4 py-2 text-sm font-medium"
            >
              {loading ? "Analyzing..." : "Analyze upload"}
            </button>
            <span className="text-slate-500 text-sm">or</span>
            <button
              disabled={loading}
              onClick={runDemo}
              className="rounded-lg border border-slate-700 hover:border-slate-500 disabled:opacity-40 transition px-4 py-2 text-sm font-medium"
            >
              {loading ? "Running..." : "Run demo mode"}
            </button>
          </div>

          {error && <p className="mt-3 text-sm text-alert-500">{error}</p>}

          {session && (
            <div className="mt-4 text-sm text-slate-400">
              Last session <code>{session.id}</code> ({session.source_filename}) — {session.status} —{" "}
              {session.total_vehicles} vehicle(s), {session.speeding_count} speeding
            </div>
          )}
        </section>

        <section className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <KpiCard label="Total vehicles" value={summary?.total_vehicles ?? "-"} />
          <KpiCard label="Average speed" value={summary ? `${summary.average_speed_kmh} km/h` : "-"} />
          <KpiCard label="Max speed" value={summary ? `${summary.max_speed_kmh} km/h` : "-"} />
          <KpiCard label="Speeding events" value={summary?.speeding_count ?? "-"} accent="alert" />
          <KpiCard label="Sessions analyzed" value={summary?.total_sessions ?? "-"} />
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="font-semibold mb-4">Recent vehicle speeds</h2>
          {chartData.length === 0 ? (
            <p className="text-sm text-slate-500">No events yet — run the demo or upload a video above.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
                <Bar dataKey="speed" radius={[4, 4, 0, 0]}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.speeding ? "#dc2626" : "#16a34a"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Event history</h2>
            <a
              href={api.exportCsvUrl()}
              className="text-sm rounded-lg border border-slate-700 hover:border-slate-500 transition px-3 py-1.5"
            >
              Export CSV
            </a>
          </div>
          {events.length === 0 ? (
            <p className="text-sm text-slate-500">No events recorded yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-800">
                    <th className="py-2 pr-4">Vehicle</th>
                    <th className="py-2 pr-4">Class</th>
                    <th className="py-2 pr-4">Est. speed</th>
                    <th className="py-2 pr-4">Limit</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((e) => (
                    <tr key={e.id} className="border-b border-slate-800/60">
                      <td className="py-2 pr-4">#{e.vehicle_track_id}</td>
                      <td className="py-2 pr-4 capitalize">{e.vehicle_class}</td>
                      <td className="py-2 pr-4">{e.estimated_speed_kmh} km/h</td>
                      <td className="py-2 pr-4">{e.speed_limit_kmh} km/h</td>
                      <td className="py-2 pr-4">
                        {e.is_speeding ? (
                          <span className="text-alert-500 font-medium">Speeding</span>
                        ) : (
                          <span className="text-brand-500">OK</span>
                        )}
                      </td>
                      <td className="py-2 pr-4 text-slate-500">{new Date(e.timestamp).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
