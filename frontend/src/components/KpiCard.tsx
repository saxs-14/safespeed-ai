interface Props {
  label: string;
  value: string | number;
  accent?: "default" | "alert";
}

export default function KpiCard({ label, value, accent = "default" }: Props) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1.5 text-2xl font-bold ${accent === "alert" ? "text-alert-500" : "text-slate-100"}`}>
        {value}
      </p>
    </div>
  );
}
