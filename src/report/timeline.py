"""Self-contained, customer-readable evidence timeline for CutoverProof."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Optional

from src.scenarios.models import ExecutionTrace, RunResult


class TimelineRenderer:
    """Render a portable HTML safety case from recorded execution evidence."""

    def __init__(self, output_dir: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.output_dir = Path(output_dir) if output_dir else base_dir / "artifacts" / "timelines"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_timeline_html(
        self,
        run_result: RunResult,
        failing_trace: Optional[ExecutionTrace] = None,
        repaired_trace: Optional[ExecutionTrace] = None,
    ) -> Path:
        trace = failing_trace or next(
            (item for item in run_result.traces if item.has_violation),
            run_result.traces[-1] if run_result.traces else None,
        )
        repair_trace = repaired_trace or run_result.repair_replay_trace
        out_path = self.output_dir / f"{run_result.run_id}_timeline.html"
        out_path.write_text(self._build_html(run_result, trace, repair_trace), encoding="utf-8")
        return out_path

    @staticmethod
    def _evidence_table(trace: ExecutionTrace) -> str:
        rows = trace.failing_evidence_rows
        if not rows:
            return "<p class='empty'>No violating rows were returned.</p>"
        columns = list(dict.fromkeys(key for row in rows for key in row))
        head = "".join(f"<th>{html.escape(column.replace('_', ' '))}</th>" for column in columns)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(row.get(column, '—')))}</td>" for column in columns) + "</tr>"
            for row in rows
        )
        return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"

    @staticmethod
    def _trace_steps(trace: Optional[ExecutionTrace], repaired: bool = False) -> str:
        if not trace or not trace.step_outcomes:
            return "<p class='empty'>No executed steps were recorded.</p>"
        cards: list[str] = []
        for step in trace.step_outcomes:
            cards.append(
                f"""
                <li class="step">
                  <span class="step-number">{step.step_index}</span>
                  <div class="step-copy">
                    <strong>{html.escape(step.operation_id.replace('_', ' ').title())}</strong>
                    <span>{html.escape(step.actor)} · {html.escape(step.phase.title())} · {step.duration_ms:.1f} ms</span>
                    <details><summary>View executed SQL</summary><pre>{html.escape(step.sql_executed)}</pre></details>
                  </div>
                  <span class="step-status {'pass' if repaired else ''}">Executed</span>
                </li>
                """
            )
        return f"<ol class='steps'>{''.join(cards)}</ol>"

    def _build_html(
        self,
        run_result: RunResult,
        trace: Optional[ExecutionTrace],
        repair_trace: Optional[ExecutionTrace],
    ) -> str:
        scenario = html.escape(run_result.scenario_name)
        model = html.escape(run_result.model_name or "No model")
        provider = html.escape(run_result.model_provider or run_result.reasoning_backend)
        run_id = html.escape(run_result.run_id)
        unsafe = run_result.verified_counterexample_found
        decision = "DO NOT CUT OVER" if unsafe else "NO VIOLATION FOUND"
        decision_class = "danger" if unsafe else "safe"
        hypothesis = html.escape(trace.hypothesis if trace else "No candidate hypothesis recorded")
        boundary = html.escape(trace.first_violating_boundary if trace and trace.first_violating_boundary else "No violated invariant")
        failing_steps = self._trace_steps(trace)
        evidence = self._evidence_table(trace) if trace else "<p class='empty'>No evidence rows were recorded.</p>"
        trace_eyebrow = "Failing execution" if unsafe else "Bounded search result"
        trace_title = "The ordering that broke the migration" if unsafe else "No violating ordering was found"
        trace_badge = "COUNTEREXAMPLE" if unsafe else "INCONCLUSIVE"
        trace_badge_class = "danger" if unsafe else "safe"
        trace_copy = (
            "Each operation below was executed against a clean PostgreSQL database in this order."
            if unsafe
            else "The final recorded candidate is shown below. No declared invariant returned a violating row within the search budget."
        )
        evidence_panel = (
            f"<div class='evidence-grid'><div class='evidence-summary'><span>Failed SQL check</span><strong>{boundary}</strong></div><div><p class='eyebrow'>Rows returned by the invariant</p>{evidence}</div></div>"
            if unsafe
            else "<div class='replay-result'><span>Verifier result</span><strong>0 violating rows in the recorded candidate</strong></div>"
        )

        replay = ""
        if repair_trace:
            replay_state = "VERIFIED" if not repair_trace.has_violation else "STILL FAILING"
            replay_class = "safe" if not repair_trace.has_violation else "danger"
            replay = f"""
            <section class="card replay-card">
              <div class="section-heading">
                <div><p class="eyebrow">Human-approved replay</p><h2>Same schedule, repaired sandbox</h2></div>
                <span class="pill {replay_class}">{replay_state}</span>
              </div>
              <p class="section-copy">The approved repair was applied to a clean database, then the identical failing ordering was executed again.</p>
              {self._trace_steps(repair_trace, repaired=True)}
              <div class="replay-result"><span>SQL invariant</span><strong>{'0 violating rows' if not repair_trace.has_violation else 'Violation remains'}</strong></div>
            </section>
            """

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CutoverProof execution timeline — {scenario}</title>
  <style>
    :root {{ --ink:#0d1227; --muted:#687087; --line:#dfe3ee; --brand:#3847e9; --brand-soft:#f1f3ff; --danger:#d93430; --danger-soft:#fff2f1; --safe:#16845b; --safe-soft:#edf9f4; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f6f7fb; color:var(--ink); font-family:"Alegreya Sans",Inter,ui-sans-serif,system-ui,sans-serif; }}
    .page {{ width:min(1180px,calc(100% - 40px)); margin:36px auto 64px; }}
    .topline {{ margin-bottom:18px; display:flex; align-items:center; justify-content:space-between; gap:18px; }}
    .brand {{ display:flex; align-items:center; gap:10px; font-family:Georgia,serif; font-size:25px; font-weight:700; }}
    .mark {{ width:34px; height:34px; border:7px solid var(--brand); border-radius:50% 50% 50% 8px; transform:rotate(-45deg); }}
    .run-id {{ color:var(--muted); font:12px ui-monospace,SFMono-Regular,Consolas,monospace; overflow-wrap:anywhere; }}
    .card {{ margin-top:18px; padding:30px; border:1px solid var(--line); border-radius:16px; background:#fff; box-shadow:0 12px 34px rgba(20,27,61,.06); }}
    .hero {{ padding:36px; }}
    .hero-grid,.section-heading {{ display:flex; align-items:flex-start; justify-content:space-between; gap:28px; }}
    .eyebrow {{ margin:0 0 7px; color:var(--brand); font-size:12px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; }}
    h1,h2 {{ margin:0; font-family:Georgia,"Times New Roman",serif; letter-spacing:-.4px; }}
    h1 {{ max-width:800px; font-size:clamp(34px,5vw,58px); line-height:1.02; }}
    h2 {{ font-size:30px; }}
    .hero-copy,.section-copy {{ color:var(--muted); font-size:17px; line-height:1.5; }}
    .hero-copy {{ max-width:760px; margin:18px 0 0; }}
    .pill {{ display:inline-flex; align-items:center; min-height:44px; padding:0 17px; border:1px solid; border-radius:9px; font-size:14px; font-weight:800; white-space:nowrap; }}
    .pill.danger {{ color:var(--danger); border-color:#f0b6b3; background:var(--danger-soft); }}
    .pill.safe {{ color:var(--safe); border-color:#b8ddcf; background:var(--safe-soft); }}
    .facts {{ margin-top:28px; padding-top:22px; border-top:1px solid var(--line); display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:16px; }}
    .facts div {{ min-width:0; }} .facts span {{ display:block; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.6px; }} .facts strong {{ display:block; margin-top:5px; overflow-wrap:anywhere; }}
    .finding {{ margin-top:22px; padding:18px 20px; border-left:4px solid var(--danger); background:var(--danger-soft); }}
    .finding span {{ display:block; color:#9f2926; font-size:12px; font-weight:800; text-transform:uppercase; }} .finding strong {{ display:block; margin-top:5px; font-size:20px; }}
    .section-copy {{ margin:10px 0 24px; }}
    .steps {{ margin:0; padding:0; list-style:none; display:grid; gap:10px; }}
    .step {{ padding:14px 16px; border:1px solid var(--line); border-radius:10px; display:grid; grid-template-columns:34px minmax(0,1fr) auto; align-items:center; gap:13px; }}
    .step-number {{ width:30px; height:30px; border-radius:50%; background:var(--brand-soft); color:var(--brand); display:grid; place-items:center; font-weight:800; }}
    .step-copy {{ min-width:0; display:grid; gap:3px; }} .step-copy > span {{ color:var(--muted); font-size:13px; }}
    .step-status {{ color:var(--danger); font-size:12px; font-weight:800; }} .step-status.pass {{ color:var(--safe); }}
    details {{ margin-top:6px; }} summary {{ width:max-content; color:var(--brand); font-size:12px; font-weight:700; cursor:pointer; }}
    pre {{ margin:8px 0 0; padding:12px; overflow:auto; border-radius:7px; background:#f6f7fb; color:#26304c; font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace; white-space:pre-wrap; overflow-wrap:anywhere; }}
    .evidence-grid {{ margin-top:28px; display:grid; grid-template-columns:minmax(0,.72fr) minmax(0,1.28fr); gap:18px; }}
    .evidence-summary {{ padding:20px; border-radius:11px; background:var(--danger-soft); }} .evidence-summary span {{ color:#a62c28; font-size:12px; font-weight:800; text-transform:uppercase; }} .evidence-summary strong {{ display:block; margin-top:7px; font-size:18px; overflow-wrap:anywhere; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:10px; }} table {{ width:100%; border-collapse:collapse; min-width:500px; }} th,td {{ padding:12px 13px; border-bottom:1px solid var(--line); text-align:left; }} th {{ background:#f7f8fc; color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.5px; }} td {{ font:13px ui-monospace,SFMono-Regular,Consolas,monospace; }} tbody tr:last-child td {{ border-bottom:0; }}
    .replay-card {{ border-color:#badfd1; }} .replay-result {{ margin-top:18px; padding:15px 17px; border-radius:9px; background:var(--safe-soft); display:flex; justify-content:space-between; gap:15px; color:var(--safe); }}
    .empty {{ margin:0; padding:16px; color:var(--muted); background:#f7f8fb; }}
    footer {{ margin-top:22px; color:var(--muted); font-size:12px; text-align:center; }}
    @media (max-width:760px) {{ .page {{ width:min(100% - 20px,1180px); margin-top:18px; }} .card,.hero {{ padding:21px; }} .hero-grid,.section-heading {{ display:grid; }} .facts {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .evidence-grid {{ grid-template-columns:1fr; }} .step {{ grid-template-columns:32px minmax(0,1fr); }} .step-status {{ grid-column:2; }} .run-id {{ display:none; }} }}
  </style>
</head>
<body>
  <main class="page">
    <div class="topline"><div class="brand"><span class="mark"></span>CutoverProof</div><div class="run-id">Run {run_id}</div></div>
    <section class="card hero">
      <div class="hero-grid"><div><p class="eyebrow">Executed migration assessment</p><h1>{scenario}</h1><p class="hero-copy">A portable record of the exact schedule, database check, evidence rows, and approved replay behind this decision.</p></div><span class="pill {decision_class}">{decision}</span></div>
      <div class="facts">
        <div><span>Approach</span><strong>{html.escape(run_result.approach_id)}</strong></div>
        <div><span>Search</span><strong>{run_result.candidates_attempted} / {run_result.max_budget} candidates</strong></div>
        <div><span>Model</span><strong>{model}<br>{provider}</strong></div>
        <div><span>Usage</span><strong>{run_result.model_calls} calls / {run_result.model_tokens:,} tokens<br>Cost not calculated</strong></div>
        <div><span>Runtime</span><strong>{run_result.wall_clock_seconds:.2f}s</strong></div>
      </div>
      <div class="finding"><span>Candidate hypothesis</span><strong>{hypothesis}</strong></div>
    </section>
    <section class="card">
      <div class="section-heading"><div><p class="eyebrow">{trace_eyebrow}</p><h2>{trace_title}</h2></div><span class="pill {trace_badge_class}">{trace_badge}</span></div>
      <p class="section-copy">{trace_copy}</p>
      {failing_steps}
      {evidence_panel}
    </section>
    {replay}
    <footer>Generated from recorded CutoverProof run evidence · No production database access</footer>
  </main>
</body>
</html>"""
