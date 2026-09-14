import { Link } from "react-router-dom";

const FEATURES = [
  { title: "Vehicle detection", desc: "Detects cars, buses, motorbikes and bicycles in uploaded footage." },
  { title: "Multi-object tracking", desc: "Follows each vehicle frame-to-frame with a lightweight centroid tracker." },
  { title: "Speed estimation", desc: "Converts pixel displacement to km/h using a configurable calibration." },
  { title: "Overspeed alerts", desc: "Flags vehicles above a configurable speed limit, per zone." },
  { title: "Evidence capture", desc: "Saves a cropped frame per detected vehicle for review." },
  { title: "CSV export & dashboard", desc: "Live KPIs, event history and one-click CSV export." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between px-6 py-5 max-w-6xl mx-auto">
        <div className="flex items-center gap-2 font-semibold text-lg">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-brand-500" />
          SafeSpeed AI
        </div>
        <Link
          to="/app"
          className="rounded-lg bg-brand-600 hover:bg-brand-500 transition px-4 py-2 text-sm font-medium"
        >
          Open dashboard
        </Link>
      </header>

      <main className="max-w-6xl mx-auto px-6">
        <section className="py-16 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
            AI-powered road safety, <span className="text-brand-500">from any camera</span>
          </h1>
          <p className="mt-5 text-slate-400 max-w-2xl mx-auto text-lg">
            Upload traffic footage and SafeSpeed AI detects vehicles, tracks them across frames and
            estimates their speed — flagging dangerous driving automatically.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Link to="/app" className="rounded-lg bg-brand-600 hover:bg-brand-500 transition px-5 py-3 font-medium">
              Try the live demo
            </Link>
            <a
              href="#how-it-works"
              className="rounded-lg border border-slate-700 hover:border-slate-500 transition px-5 py-3 font-medium"
            >
              How it works
            </a>
          </div>
          <p className="mt-4 text-xs text-slate-500">
            Speeds shown by this MVP are <strong>estimated</strong>, not legal-grade enforcement measurements —
            see the README for calibration details.
          </p>
        </section>

        <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 py-8">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
              <h3 className="font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-slate-400">{f.desc}</p>
            </div>
          ))}
        </section>

        <section id="how-it-works" className="py-16">
          <h2 className="text-2xl font-bold mb-6">How it works</h2>
          <ol className="grid sm:grid-cols-4 gap-4 text-sm">
            {[
              "Upload a traffic video (or run the bundled demo clip)",
              "MobileNet-SSD detects vehicles frame by frame",
              "A centroid tracker follows each vehicle across frames",
              "Displacement + calibration → estimated speed, flagged if over the limit",
            ].map((step, i) => (
              <li key={i} className="rounded-xl bg-slate-900/60 border border-slate-800 p-4">
                <span className="text-brand-500 font-bold">{i + 1}.</span> {step}
              </li>
            ))}
          </ol>
        </section>

        <section className="py-16 grid sm:grid-cols-2 gap-8">
          <div>
            <h2 className="text-2xl font-bold mb-3">Who it's for</h2>
            <ul className="text-slate-400 space-y-1.5 text-sm">
              <li>Schools monitoring traffic near pickup/drop-off zones</li>
              <li>Security companies protecting private estates</li>
              <li>Fleet & logistics operators tracking driver behaviour</li>
              <li>Municipalities without budget for radar-based enforcement</li>
              <li>Road safety NGOs gathering evidence for advocacy</li>
            </ul>
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-3">Pricing model</h2>
            <ul className="text-slate-400 space-y-1.5 text-sm">
              <li>Per-camera monthly SaaS subscription</li>
              <li>Fleet-wide monitoring bundle</li>
              <li>One-time installation + hardware package</li>
              <li>Municipal multi-site contracts</li>
            </ul>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        SafeSpeed AI — road safety MVP. Not certified for legal enforcement use.
      </footer>
    </div>
  );
}
