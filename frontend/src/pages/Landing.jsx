import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-10 py-6 border-b border-line">
        <span className="font-display italic text-2xl">CareerAI</span>
        <nav className="flex items-center gap-6 text-sm text-muted">
          <Link to="/login" className="hover:text-paper transition-colors">
            Log in
          </Link>
          <Link
            to="/signup"
            className="text-paper border border-line px-4 py-2 rounded-sm hover:border-amber hover:text-amber transition-colors"
          >
            Get started
          </Link>
        </nav>
      </header>

      <section className="grid md:grid-cols-2 gap-16 px-10 py-20 max-w-6xl mx-auto items-center">
        <div>
          <p className="text-sm text-muted mb-4 font-mono">For students & early-career engineers</p>
          <h1 className="font-display text-6xl leading-[1.05] mb-6">
            Your AI career &amp; interview assistant.
          </h1>
          <p className="text-muted text-lg leading-relaxed mb-8 max-w-md">
            Upload your CV, match it against real job postings, close your
            skill gaps with a personal roadmap, and rehearse the interview
            before it counts.
          </p>
          <Link
            to="/signup"
            className="inline-block bg-amber text-ink px-6 py-3 rounded-sm font-medium hover:opacity-90 transition-opacity"
          >
            Get started
          </Link>
        </div>

        <div className="bg-surface border border-line p-6">
          <p className="font-mono text-xs text-amber mb-5">PERSONALIZED ANALYSIS</p>
          <h2 className="font-display text-3xl text-paper mb-4">Your data, not a demo.</h2>
          <p className="text-sm text-muted leading-relaxed mb-6">
            CareerAI analyzes your uploaded CV, saved skills, target role, and the job description you provide.
          </p>
          <div className="border-t border-line pt-4 text-sm text-teal">Set your target role to begin.</div>
        </div>
      </section>

      <section className="border-t border-line px-10 py-16 max-w-6xl mx-auto">
        <div className="grid md:grid-cols-3 gap-10">
          {[
            {
              title: "Job matching",
              body: "Paste a job description and see exactly which of your skills match and which you're missing.",
            },
            {
              title: "Career roadmap",
              body: "A week-by-week plan for closing the specific gaps between where you are and your target role.",
            },
            {
              title: "Interview practice",
              body: "Rehearse with an AI interviewer for your target role, then review a scored breakdown by category.",
            },
          ].map((f) => (
            <div key={f.title} className="border-l-[3px] border-line pl-5">
              <h3 className="text-paper mb-2">{f.title}</h3>
              <p className="text-sm text-muted leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
