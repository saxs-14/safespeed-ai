const API_BASE = "";
const API_KEY = (import.meta.env.VITE_API_KEY as string) || "dev-local-key-change-me";

export interface SpeedEvent {
  id: number;
  session_id: string;
  vehicle_track_id: number;
  vehicle_class: string;
  estimated_speed_kmh: number;
  speed_limit_kmh: number;
  is_speeding: boolean;
  frame_number: number;
  timestamp: string;
  evidence_path: string | null;
}

export interface AnalysisSession {
  id: string;
  source_filename: string;
  speed_limit_kmh: number;
  pixels_per_meter: number;
  calibrated: boolean;
  total_vehicles: number;
  max_speed_kmh: number;
  avg_speed_kmh: number;
  speeding_count: number;
  status: string;
  created_at: string;
}

export interface DashboardSummary {
  total_vehicles: number;
  average_speed_kmh: number;
  max_speed_kmh: number;
  speeding_count: number;
  total_sessions: number;
  speed_limit_kmh: number;
}

function authHeaders(): HeadersInit {
  return { "X-API-Key": API_KEY };
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
  }
  return res.json();
}

async function downloadFile(url: string, filename: string) {
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

export const api = {
  health: () => fetch(`${API_BASE}/api/health`).then((r) => json<{ status: string }>(r)),

  summary: () =>
    fetch(`${API_BASE}/api/dashboard/summary`, { headers: authHeaders() }).then((r) => json<DashboardSummary>(r)),

  events: (sessionId?: string) =>
    fetch(`${API_BASE}/api/events${sessionId ? `?session_id=${sessionId}` : ""}`, { headers: authHeaders() }).then(
      (r) => json<SpeedEvent[]>(r)
    ),

  exportEvents: (sessionId?: string) =>
    downloadFile(
      `${API_BASE}/api/events/export${sessionId ? `?session_id=${sessionId}` : ""}`,
      "safespeed_events.csv"
    ),

  runDemo: (speedLimit: number, pxPerMeter: number) => {
    const form = new FormData();
    form.set("speed_limit_kmh", String(speedLimit));
    form.set("pixels_per_meter", String(pxPerMeter));
    return fetch(`${API_BASE}/api/analyze/demo`, { method: "POST", headers: authHeaders(), body: form }).then((r) =>
      json<AnalysisSession>(r)
    );
  },

  analyzeVideo: (file: File, speedLimit: number, pxPerMeter: number, calibrated: boolean) => {
    const form = new FormData();
    form.set("file", file);
    form.set("speed_limit_kmh", String(speedLimit));
    form.set("pixels_per_meter", String(pxPerMeter));
    form.set("calibrated", String(calibrated));
    return fetch(`${API_BASE}/api/analyze`, { method: "POST", headers: authHeaders(), body: form }).then((r) =>
      json<AnalysisSession>(r)
    );
  },
};
