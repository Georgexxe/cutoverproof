import {
  ArrowPathIcon, ArrowRightIcon, ArrowUpTrayIcon, CheckCircleIcon, CheckIcon, Cog6ToothIcon,
  ChevronDownIcon, ChevronRightIcon, CircleStackIcon, ClockIcon, CodeBracketSquareIcon,
  ExclamationTriangleIcon, HomeIcon, InformationCircleIcon, LockClosedIcon, PlayIcon, PlusIcon,
  QueueListIcon, ShieldCheckIcon, UserCircleIcon, XMarkIcon,
} from "@heroicons/react/24/outline";
import { useCallback, useEffect, useId, useMemo, useRef, useState, type FormEvent } from "react";
import { apiRequest, setCsrfToken } from "./lib/api";
import {
  registerCutoverProofTools,
  WEBMCP_OPEN_REPAIR,
  WEBMCP_REVIEW_CREATED,
} from "./webmcp";
import type { ChangeReviewDraft, ConnectionSummary, ConnectionsResponse, Health, JobState, RunDetail, RunSummary, ScenarioSummary, Session, View, WebMcpAvailability } from "./types";

const NAV_ITEMS: Array<{ id: View; label: string; icon: typeof HomeIcon }> = [
  { id: "overview", label: "Home", icon: HomeIcon },
  { id: "assessments", label: "Assessments", icon: ShieldCheckIcon },
  { id: "settings", label: "Settings", icon: Cog6ToothIcon },
];

type AppPreferences = {
  candidateBudget: number;
  autoOpenEvidence: boolean;
};

const DEFAULT_PREFERENCES: AppPreferences = {
  candidateBudget: 4,
  autoOpenEvidence: false,
};

function LoginView({ onSignedIn }: { onSignedIn: (session: Session) => void }) {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setBusy(true); setError(null); try { onSignedIn(await apiRequest<Session>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) })); } catch (reason) { setError(reason instanceof Error ? reason.message : "Sign-in failed."); } finally { setBusy(false); } };
  return <main className="login-page">
    <section className="login-story">
      <span className="brand-mark"><ShieldCheckIcon />CutoverProof</span>
      <div className="login-pitch">
        <p className="eyebrow">PostgreSQL migration testing</p>
        <h1>Catch migration failures before production.</h1>
        <p>Test your migration safely, see exactly what failed, and verify the fix before you deploy.</p>
      </div>
      <ul aria-label="Product safeguards">
        <li><CheckCircleIcon />Isolated test database</li>
        <li><CheckCircleIcon />You approve every fix</li>
        <li><CheckCircleIcon />Reproducible results</li>
      </ul>
    </section>
    <section className="login-panel" aria-label="Sign in">
      <form className="login-card" onSubmit={submit}>
        <span className="mobile-login-brand" aria-hidden="true">CutoverProof</span>
        <p className="eyebrow">Welcome back</p>
        <h2>Sign in</h2>
        <p>Open your workspace.</p>
        <label>Email<input type="email" autoComplete="username" placeholder="you@company.com" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Password<input type="password" autoComplete="current-password" placeholder="Enter your password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <button className="primary-button login-button" disabled={busy}>{busy ? "Signing in…" : "Sign in"}<ArrowRightIcon /></button>
      </form>
    </section>
  </main>;
}

function useWorkspaceData(active: boolean) {
  const [health, setHealth] = useState<Health | null>(null); const [runs, setRuns] = useState<RunSummary[]>([]); const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]); const [connections, setConnections] = useState<ConnectionsResponse | null>(null); const [initializing, setInitializing] = useState(true);
  const refreshRuns = useCallback(async () => setRuns(await apiRequest<RunSummary[]>("/api/runs")), []); const refreshScenarios = useCallback(async () => setScenarios(await apiRequest<ScenarioSummary[]>("/api/scenarios")), []); const refreshConnections = useCallback(async () => setConnections(await apiRequest<ConnectionsResponse>("/api/connections")), []);
  useEffect(() => { if (!active) return; let cancelled = false; Promise.all([apiRequest<Health>("/api/health"), apiRequest<RunSummary[]>("/api/runs"), apiRequest<ScenarioSummary[]>("/api/scenarios"), apiRequest<ConnectionsResponse>("/api/connections")]).then(([nextHealth, nextRuns, nextScenarios, nextConnections]) => { if (cancelled) return; setHealth(nextHealth); setRuns(nextRuns); setScenarios(nextScenarios); setConnections(nextConnections); }).finally(() => { if (!cancelled) setInitializing(false); }); return () => { cancelled = true; }; }, [active]);
  return { health, runs, scenarios, connections, initializing, refreshRuns, refreshScenarios, refreshConnections };
}

function AppShell({ view, email, onView, onNew, onLogout, children }: { view: View; email: string; onView: (view: View) => void; onNew: () => void; onLogout: () => void; children: React.ReactNode }) {
  const [accountOpen, setAccountOpen] = useState(false);
  const accountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const dismiss = (event: PointerEvent) => {
      if (accountRef.current && !accountRef.current.contains(event.target as Node)) setAccountOpen(false);
    };
    const escape = (event: KeyboardEvent) => { if (event.key === "Escape") setAccountOpen(false); };
    document.addEventListener("pointerdown", dismiss);
    window.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", dismiss); window.removeEventListener("keydown", escape); };
  }, []);

  const changeView = (next: View) => { setAccountOpen(false); onView(next); };

  return <div className="app-shell"><aside className="sidebar"><button className="wordmark" aria-label="CutoverProof home" onClick={() => changeView("overview")}><ShieldCheckIcon /><span>CutoverProof</span></button><nav className="nav-list" aria-label="Primary navigation">{NAV_ITEMS.map((item) => { const Icon = item.icon; const active = view === item.id || (item.id === "assessments" && view === "assessment"); return <button key={item.id} data-tour={item.id === "assessments" ? "assessments-navigation" : undefined} aria-label={item.label} className={`nav-item ${active ? "active" : ""}`} onClick={() => changeView(item.id)}><Icon /><span>{item.label}</span></button>; })}</nav></aside><div className="workspace"><header className="topbar"><div className="topbar-actions"><div className="menu-wrap" ref={accountRef}><button className="icon-button" aria-label="Account menu" aria-expanded={accountOpen} onClick={() => setAccountOpen((open) => !open)}><UserCircleIcon /></button>{accountOpen ? <div className="menu-card account-menu"><span>Signed in as</span><strong>{email}</strong><button onClick={() => changeView("settings")}>Account settings</button><button onClick={onLogout}>Sign out</button></div> : null}</div></div></header>{children}</div></div>;
}

function AssessmentHistoryView({ runs, onNew, onSelect }: { runs: RunSummary[]; onNew: () => void; onSelect: (runId: string) => void }) {
  if (!runs.length) return <main className="main-content list-view assessment-history"><div className="simple-page-heading"><div><h1>Assessments</h1><p>Your completed migration checks will appear here.</p></div></div><section className="assessment-empty"><span><ShieldCheckIcon /></span><h2>No assessments yet</h2><p>Run your first assessment to see its decision and evidence here.</p><button className="primary-button" onClick={onNew}><PlusIcon />New assessment</button></section></main>;
  return <main className="main-content list-view assessment-history"><div className="simple-page-heading"><div><h1>Assessments</h1><p>Your migration decisions and evidence.</p></div><button className="primary-button" onClick={onNew}><PlusIcon />New assessment</button></div><div className="run-table"><div className="table-row table-head"><span>Migration</span><span>Decision</span><span>Checked</span><span /></div>{runs.map((item) => <div className="table-row" key={item.run_id}><span><strong>{item.title}</strong><small>{item.scenario_name}</small></span><span className={`table-status ${item.status}`}>{item.status_label}</span><span>{item.candidates_attempted} of {item.max_budget}</span><button onClick={() => onSelect(item.run_id)} aria-label={`Open ${item.title}`}>Open <ChevronRightIcon /></button></div>)}</div></main>;
}

function SettingsView({
  email,
  health,
  connection,
  webMcp,
  preferences,
  onSave,
  onLogout,
}: {
  email: string;
  health: Health | null;
  connection: ConnectionSummary | null;
  webMcp: WebMcpAvailability;
  preferences: AppPreferences;
  onSave: (preferences: AppPreferences) => void;
  onLogout: () => void;
}) {
  const [draft, setDraft] = useState(preferences);
  const [saved, setSaved] = useState(false);
  const dirty = draft.candidateBudget !== preferences.candidateBudget || draft.autoOpenEvidence !== preferences.autoOpenEvidence;

  useEffect(() => setDraft(preferences), [preferences]);

  const save = () => {
    onSave(draft);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2200);
  };

  const reset = () => {
    setDraft(DEFAULT_PREFERENCES);
    onSave(DEFAULT_PREFERENCES);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2200);
  };

  return <main className="main-content list-view settings-view">
    <div className="simple-page-heading settings-heading">
      <div><h1>Settings</h1><p>Defaults, safeguards, and account.</p></div>
      <button className="primary-button settings-save" disabled={!dirty} onClick={save}><CheckIcon />{saved ? "Saved" : "Save changes"}</button>
    </div>

    <div className="settings-layout">
      <div className="settings-main">
        <section className="settings-section settings-preferences">
          <div className="settings-section-heading"><span className="settings-icon"><Cog6ToothIcon /></span><div><h2>Assessment defaults</h2><p>Used for new migrations.</p></div></div>
          <div className="settings-control-row">
            <label htmlFor="candidate-budget"><strong>Schedules to test</strong><span>More schedules can uncover more ordering risks.</span></label>
            <select id="candidate-budget" value={draft.candidateBudget} onChange={(event) => setDraft((current) => ({ ...current, candidateBudget: Number(event.target.value) }))}>
              {[2, 4, 6, 8].map((value) => <option key={value} value={value}>{value} candidates</option>)}
            </select>
          </div>
          <div className="settings-control-row">
            <div><strong>Open evidence after a run</strong><span>Show the failing order and rows immediately.</span></div>
            <button type="button" role="switch" aria-checked={draft.autoOpenEvidence} aria-label="Open evidence after a run" className={`toggle-control ${draft.autoOpenEvidence ? "on" : ""}`} onClick={() => setDraft((current) => ({ ...current, autoOpenEvidence: !current.autoOpenEvidence }))}><span /></button>
          </div>
          <footer className="settings-section-footer"><button className="text-button" onClick={reset}><ArrowPathIcon />Reset defaults</button>{saved ? <span className="saved-note"><CheckCircleIcon />Preferences saved</span> : null}</footer>
        </section>

        <section className="settings-section">
          <div className="settings-section-heading"><span className="settings-icon safe"><ShieldCheckIcon /></span><div><h2>Safeguards</h2><p>Always on.</p></div></div>
          <dl className="settings-status-list">
            <div><dt><strong>Test database</strong><span>Reset before every schedule.</span></dt><dd><span className="status-dot" />Isolated</dd></div>
            <div><dt><strong>Production access</strong><span>Production targets are refused.</span></dt><dd><LockClosedIcon />Blocked</dd></div>
            <div><dt><strong>Repairs</strong><span>You approve before replay.</span></dt><dd><UserCircleIcon />Human only</dd></div>
          </dl>
        </section>
      </div>

      <aside className="settings-aside">
        <section className="settings-section runtime-card">
          <div className="settings-section-heading"><span className="settings-icon"><CircleStackIcon /></span><div><h2>System</h2><p>Ready for new assessments.</p></div></div>
          <dl className="runtime-list">
            <div><dt>Test database</dt><dd><span className="status-dot" />{connection ? "Ready" : "Checking"}</dd></div>
            <div><dt>Risk planner</dt><dd><span className={`status-dot ${health?.model_configured ? "" : "warning"}`} />{health?.model_configured ? "Ready" : "Offline"}</dd></div>
            <div><dt>Browser agent</dt><dd><span className={`status-dot ${webMcp.ready ? "" : "warning"}`} />{webMcp.ready ? "Connected" : "Standard mode"}</dd></div>
          </dl>
          <p className="runtime-note">The browser agent can prepare reviews and read evidence. It cannot run migrations or approve repairs.</p>
        </section>

        <section className="settings-section account-card">
          <div className="settings-section-heading"><span className="settings-icon neutral"><UserCircleIcon /></span><div><h2>Account</h2><p>Current session.</p></div></div>
          <div className="account-identity"><span>{email.slice(0, 1).toUpperCase() || "E"}</span><div><strong>{email}</strong><small>Backend engineer</small></div></div>
          <button className="secondary-button signout-button" onClick={onLogout}>Sign out</button>
        </section>
      </aside>
    </div>
  </main>;
}

function ConnectionsView({ data, onRefresh, onSelect }: { data: ConnectionsResponse | null; onRefresh: () => Promise<void>; onSelect: (connection: ConnectionSummary) => void }) {
  const [formOpen, setFormOpen] = useState(false); const [busy, setBusy] = useState(false); const [message, setMessage] = useState<string | null>(null);
  const submit = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setBusy(true); setMessage(null); const form = new FormData(event.currentTarget); try { const connection = await apiRequest<ConnectionSummary>("/api/connections/test", { method: "POST", body: JSON.stringify({ host: form.get("host"), port: Number(form.get("port")), database: "cutoverproof_sandbox", username: "cutover", password: form.get("password"), sslmode: form.get("sslmode"), confirm_disposable: form.get("confirm") === "on" }) }); await onRefresh(); onSelect(connection); setFormOpen(false); setMessage(`Verified PostgreSQL ${connection.server_version}. This target will be used for new runs.`); } catch (reason) { setMessage(reason instanceof Error ? reason.message : "Connection test failed."); } finally { setBusy(false); } };
  return <main className="main-content connections-view"><div className="section-heading"><div><p className="eyebrow">Disposable execution targets</p><h1>PostgreSQL sandboxes</h1><p className="lede">CutoverProof only runs destructive resets against the exact database <code>cutoverproof_sandbox</code> using the <code>cutover</code> user.</p></div><button className="primary-button" onClick={() => setFormOpen(!formOpen)}><PlusIcon />Test connection</button></div>{message ? <div className="connection-message"><InformationCircleIcon />{message}</div> : null}{formOpen ? <form className="connection-form" onSubmit={submit}><div className="form-heading"><div><p className="eyebrow">Memory-only profile</p><h2>Test a disposable PostgreSQL target</h2></div><button type="button" className="icon-button" onClick={() => setFormOpen(false)}><XMarkIcon /></button></div><div className="form-grid"><label>Host<input name="host" placeholder="localhost" required /></label><label>Port<input name="port" type="number" defaultValue="5432" required /></label><label>Database<input value="cutoverproof_sandbox" disabled readOnly /></label><label>User<input value="cutover" disabled readOnly /></label><label>Password<input name="password" type="password" required /></label><label>SSL mode<select name="sslmode" defaultValue="prefer"><option>prefer</option><option>require</option><option>disable</option></select></label></div><label className="confirm-row"><input name="confirm" type="checkbox" required />I confirm this target is disposable and may have its public schema reset.</label><p className="boundary-copy">Credentials remain in server memory for this demo session and never enter run artifacts. Non-local hosts must be exactly allow-listed by the server operator.</p><footer><button className="primary-button" disabled={busy}>{busy ? "Testing…" : "Test & save for session"}</button></footer></form> : null}<div className="connection-list">{data ? [data.configured, ...data.ephemeral].map((connection) => <article key={connection.id}><span className="connection-icon"><CircleStackIcon /></span><div><small>{connection.id === "configured" ? "Default target" : "Session target"}</small><h2>{connection.label}</h2><p>{connection.username}@{connection.host}:{connection.port}/{connection.database}</p></div><span className="verified-pill"><CheckCircleIcon />{connection.status}</span></article>) : <div className="loading-panel">Loading connections…</div>}</div></main>;
}

function PhaseRail({ run }: { run: RunDetail }) {
  const phases = run.phases.slice(0, 5);
  const reportedIndex = phases.findIndex((phase) => phase.failed_operation);
  const fallbackIndex = run.status === "blocked" || run.status === "repair_failed" ? phases.findIndex((phase) => phase.id === "backfill") : -1;
  const failedIndex = reportedIndex >= 0 ? reportedIndex : fallbackIndex;
  return <div className="phase-rail" aria-label="Migration phase timeline">{phases.map((phase, index) => {
    const hasConflict = index === failedIndex;
    const conflictLabel = phase.failed_operation?.replaceAll("_", " ") ?? "Conflict found";
    return <div className="phase-group" key={phase.id}><div className="phase-item"><span className="phase-name">{phase.name}</span><span className={`phase-node ${phase.state}`}>{phase.state === "complete" ? <CheckIcon /> : <ClockIcon />}</span></div>{index < phases.length - 1 ? <span className={`phase-connector ${hasConflict ? "conflict" : ""}`} /> : null}{hasConflict ? <div className="conflict-marker" aria-label={`Conflict: ${conflictLabel}`}><span className="conflict-node"><XMarkIcon /></span><i className="conflict-stem" /><b className="conflict-label">{conflictLabel}</b></div> : null}</div>;
  })}</div>;
}

function AssessmentView({ run, onApprove, onEvidence, onRetry }: { run: RunDetail; onApprove: () => void; onEvidence: () => void; onRetry: () => void }) {
  const blocked = run.status === "blocked" || run.status === "repair_failed";
  const replayed = Boolean(run.replay);
  const failed = run.status === "failed";
  const inconclusive = run.status === "inconclusive";
  const recommendationTitle = failed ? "Retry the assessment" : run.repair?.name ?? "Review the failing ordering";
  const recommendationCopy = failed
    ? "No decision was made. Retry the same migration."
    : run.repair?.description ?? "Review the executed steps before changing the migration.";
  const summary = replayed
    ? "The approved fix passed the same failing schedule."
    : failed
      ? "The assessment stopped before a decision was made."
      : inconclusive
        ? "No failure was found in this search. This is not proof of safety."
        : "A tested schedule broke your data rule.";
  return <main className="main-content assessment-view">
    <div className="breadcrumbs"><span>Assessments</span><ChevronRightIcon /><strong>{run.title}</strong></div>
    <section className="assessment-heading"><div><p className="eyebrow">Assessment result</p><h1>{run.title}</h1><p className="lede">{summary}</p></div><div className={`verdict ${blocked ? "danger" : failed ? "failed" : inconclusive ? "caution" : "verified"}`}>{blocked || failed ? <XMarkIcon /> : inconclusive ? <ClockIcon /> : <ShieldCheckIcon />}<span>{run.status_label}</span></div></section>
    <section className="decision-grid">
      <div className="finding-column"><p className="section-label">What happened</p><div className="finding-statement"><span className="finding-icon"><ExclamationTriangleIcon /></span><p>{run.finding}</p></div><div className="phase-section"><p className="section-label">Where it failed</p><PhaseRail run={run} /></div></div>
      <aside className="recommendation"><p className="section-label">{replayed ? "Verified fix" : "Next step"}</p><h2>{recommendationTitle}</h2><p>{recommendationCopy}</p>{failed ? <button className="primary-button approve-button" onClick={onRetry}><PlayIcon />Retry</button> : run.repair ? <button className="primary-button approve-button" onClick={onApprove} disabled={replayed}><ShieldCheckIcon />{replayed ? "Fix verified" : "Review fix"}</button> : null}<button className="link-button" onClick={onEvidence}>View evidence <ChevronRightIcon /></button></aside>
    </section>
    <footer className="run-summary"><span><InformationCircleIcon />{run.candidates_attempted} of {run.max_budget} schedules tested</span><i /><span><ClockIcon />{replayed ? `Replay ${run.replay?.duration_ms} ms` : `${run.wall_clock_seconds}s`}</span></footer>
  </main>;
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  const titleId = useId();
  const dialogRef = useRef<HTMLElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  useEffect(() => {
    previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    dialog?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape") { onClose(); return; }
      if (event.key !== "Tab" || !dialog) return;
      const focusable = Array.from(dialog.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'));
      if (!focusable.length) { event.preventDefault(); dialog.focus(); return; }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    const previousOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    window.addEventListener("keydown", key);
    return () => {
      window.removeEventListener("keydown", key);
      document.documentElement.style.overflow = previousOverflow;
      previousFocusRef.current?.focus();
    };
  }, [onClose]);
  return <div className="modal-backdrop" onMouseDown={onClose}><section ref={dialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby={titleId} tabIndex={-1} onMouseDown={(event) => event.stopPropagation()}><header><h2 id={titleId}>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={onClose}><XMarkIcon /></button></header>{children}</section></div>;
}

function EvidenceModal({ run, onClose }: { run: RunDetail; onClose: () => void }) { const columns = Array.from(new Set(run.evidence_rows.flatMap(Object.keys))); const checkName = (run.boundary ?? "No violation").replaceAll("_", " ").replace(/\binvariant\b/gi, "").trim(); return <Modal title="Evidence" onClose={onClose}><div className="evidence-review"><p className="evidence-intro">Recorded from the test database—not generated by the model.</p><div className="evidence-meta"><span><strong>Failed check</strong>{checkName}</span><span><strong>Runtime</strong>{run.wall_clock_seconds}s</span><span><strong>Tested</strong>{run.candidates_attempted} of {run.max_budget}</span></div><section><p className="section-label">Failing order</p>{run.steps.length ? <ol className="trace-list">{run.steps.map((step) => <li key={`${step.index}-${step.id}`}><span>{step.index}</span><div><strong>{step.description}</strong><small>{step.phase} · {step.duration_ms}ms</small></div><CheckIcon /></li>)}</ol> : <p className="empty-evidence">No failing order recorded.</p>}</section>{run.evidence_rows.length ? <section><p className="section-label">Rows that failed</p><div className="evidence-table"><div className="evidence-row evidence-head" style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(120px,1fr))` }}>{columns.map((column) => <span key={column}>{column.replaceAll("_", " ")}</span>)}</div>{run.evidence_rows.map((row, index) => <div className="evidence-row" key={index} style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(120px,1fr))` }}>{columns.map((column) => <span key={column}>{String(row[column] ?? "—")}</span>)}</div>)}</div></section> : null}<footer><button className="secondary-button" onClick={() => window.open(run.evidence_url, "_blank", "noopener,noreferrer")}>Full timeline</button><button className="primary-button" onClick={onClose}>Done</button></footer></div></Modal>; }

function ApprovalModal({ run, onClose, onApprove }: { run: RunDetail; onClose: () => void; onApprove: (name: string) => Promise<void> }) { const [name, setName] = useState(""); const [busy, setBusy] = useState(false); return <Modal title="Review fix" onClose={onClose}><form className="approval-form" onSubmit={(event) => { event.preventDefault(); setBusy(true); void onApprove(name).finally(() => setBusy(false)); }}><div className="repair-review"><p className="section-label">Proposed fix</p><h3>{run.repair?.name}</h3><p>{run.repair?.description}</p></div><ul className="safety-list"><li><CheckIcon />Sandbox only</li><li><CheckIcon />Approved SQL only</li><li><CheckIcon />Same schedule replayed</li></ul><label>Your name<input value={name} minLength={2} required onChange={(event) => setName(event.target.value)} placeholder="Name" /></label><footer><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={busy}>{busy ? "Replaying…" : "Approve & replay"}</button></footer></form></Modal>; }
function JobBanner({ job }: { job: JobState }) { const stages = ["Validate", "Plan", "Execute", "Verify", "Evidence"]; const activeIndex = job.progress < 24 ? 0 : job.progress < 40 ? 1 : job.progress < 72 ? 2 : job.progress < 88 ? 3 : 4; return <div className={`job-banner ${job.status}`} role="status" aria-live="polite"><header><span className="spinner" /><div><strong>{job.status === "failed" ? "Assessment stopped" : "Testing your migration"}</strong><p>{job.error ?? job.stage ?? "Starting the assessment"}</p></div><span>{job.progress}%</span></header><div className="job-progress-track"><i style={{ width: `${job.progress}%` }} /></div><ol>{stages.map((stage, index) => <li className={index < activeIndex ? "complete" : index === activeIndex ? "active" : ""} key={stage}><span>{index < activeIndex ? <CheckIcon /> : index + 1}</span>{stage}</li>)}</ol></div>; }

function ProductOverview({
  onTour,
  onNewAssessment,
  onDraftPrepared,
  onReviewDraft,
  onSelectRun,
  latestDraft,
  runs,
}: {
  onTour: () => void;
  onNewAssessment: () => void;
  onDraftPrepared: (draft: ChangeReviewDraft) => void;
  onReviewDraft: (scenarioId: string) => void;
  onSelectRun: (runId: string) => void;
  latestDraft: ChangeReviewDraft | null;
  runs: RunSummary[];
}) {
  type ContractSummary = ScenarioSummary;
  type ContractDetail = {
    id: string;
    name: string;
    objective: string;
    phase_order: Array<{ id: string; name: string }>;
    declared_operations: Array<{ id: string }>;
    invariants: Array<{ id: string }>;
  };
  type AgentActivity = { label: string; detail: string };

  const [agentPrompt, setAgentPrompt] = useState("Inspect the status-normalization contract and prepare a review focused on stale writes during the compatibility window.");
  const [agentBusy, setAgentBusy] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [agentReply, setAgentReply] = useState<string | null>(null);
  const [agentActivity, setAgentActivity] = useState<AgentActivity[]>([]);
  const [showComposer, setShowComposer] = useState(false);
  const blockedCount = runs.filter((item) => item.status === "blocked" || item.status === "repair_failed").length;
  const verifiedCount = runs.filter((item) => item.status === "repair_verified").length;

  const submitAgentRequest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const prompt = agentPrompt.trim();
    if (prompt.length < 12) {
      setAgentError("Describe the contract or risk you want the agent to review.");
      return;
    }
    setAgentBusy(true);
    setAgentError(null);
    setAgentReply(null);
    setAgentActivity([]);
    try {
      const contracts = await apiRequest<ContractSummary[]>("/api/webmcp/contracts");
      setAgentActivity([{ label: "Found contracts", detail: "Migration contracts ready" }]);
      const normalized = prompt.toLowerCase();
      const selected = contracts.find((contract) => normalized.includes(contract.id.toLowerCase()))
        ?? contracts.find((contract) => normalized.includes(contract.name.toLowerCase()))
        ?? contracts.find((contract) => contract.id === "u1_status_trigger_race")
        ?? contracts[0];
      if (!selected) throw new Error("No migration contracts are available.");

      const listOnly = /\b(list|show)\b/.test(normalized) && !/\b(inspect|review|prepare|draft|focus|analyse|analyze)\b/.test(normalized);
      if (listOnly) {
        setAgentReply(`Start with ${selected.name}.`);
        return;
      }

      const contract = await apiRequest<ContractDetail>(`/api/webmcp/contracts/${encodeURIComponent(selected.id)}`);
      setAgentActivity((current) => [...current, {
        label: "Checked contract",
        detail: `${contract.phase_order.length} phases · ${contract.declared_operations.length} steps · ${contract.invariants.length} check${contract.invariants.length === 1 ? "" : "s"}`,
      }]);

      const inspectOnly = /\b(inspect|analyse|analyze|explain)\b/.test(normalized) && !/\b(review|prepare|draft|focus|create)\b/.test(normalized);
      if (inspectOnly) {
        setAgentReply(`${contract.name} is ready to review. You decide whether to run it.`);
        return;
      }

      const riskMap: Array<[RegExp, string]> = [
        [/\b(stale|old write|legacy write)\b/, "stale_writes"],
        [/\b(compatibility|compat|legacy)\b/, "compatibility_window"],
        [/\b(order|ordering|sequence|cutover)\b/, "cutover_ordering"],
        [/\b(rollback|recovery)\b/, "rollback_readiness"],
        [/\b(invariant|consistency|data)\b/, "data_invariants"],
      ];
      const riskFocus = riskMap.filter(([pattern]) => pattern.test(normalized)).map(([, risk]) => risk);
      if (!riskFocus.length) riskFocus.push("compatibility_window", "cutover_ordering");
      const draft = await apiRequest<ChangeReviewDraft>("/api/webmcp/review-drafts", {
        method: "POST",
        body: JSON.stringify({
          scenario_id: contract.id,
          objective: prompt,
          risk_focus: Array.from(new Set(riskFocus)),
          idempotency_key: `in-app-agent:${crypto.randomUUID()}`,
        }),
      });
      setAgentActivity((current) => [...current, { label: "Prepared review", detail: "Draft ready · not run" }]);
      setAgentReply(`${contract.name} is ready. Nothing has run.`);
      onDraftPrepared(draft);
    } catch (reason) {
      setAgentError(reason instanceof Error ? reason.message : "The agent request could not be completed.");
    } finally {
      setAgentBusy(false);
    }
  };

  return (
    <main className="main-content overview-view workspace-home">
      <section className="dashboard-heading">
        <div>
          <p className="eyebrow">Migration safety</p>
          <h1>Know what’s safe to ship.</h1>
          <p>Test the migration. Review the evidence. Approve the fix.</p>
        </div>
        <div className="dashboard-actions">
          <button className="secondary-button" onClick={onTour}><PlayIcon />Run sample</button>
          <button className="primary-button" data-tour="new-assessment" onClick={onNewAssessment}><PlusIcon />New assessment</button>
        </div>
      </section>

      <section className="dashboard-stats" aria-label="Workspace summary">
        <article className={latestDraft ? "attention" : ""}><span>Needs review</span><strong>{latestDraft ? 1 : 0}</strong><small>{latestDraft ? "Prepared and waiting" : "You’re caught up"}</small></article>
        <article><span>Blocked</span><strong>{blockedCount}</strong><small>Changes needing a fix</small></article>
        <article><span>Verified</span><strong>{verifiedCount}</strong><small>Repairs proven in replay</small></article>
      </section>

      {latestDraft ? <section className="attention-card" aria-live="polite">
        <div className="attention-icon"><QueueListIcon /></div>
        <div className="attention-copy">
          <span>Needs your review</span>
          <h2>{latestDraft.contract_name}</h2>
          <p>{latestDraft.objective}</p>
          <small><LockClosedIcon />Not run yet</small>
        </div>
        <button className="primary-button" onClick={() => onReviewDraft(latestDraft.scenario_id)}>Review &amp; run</button>
      </section> : null}

      <section className="dashboard-grid" data-tour="how-it-works">
        <div className="recent-runs-section">
          <div className="section-heading compact-heading"><div><p className="eyebrow">Recent activity</p><h2>Assessments</h2></div></div>
          {runs.length ? <div className="assessment-list compact-assessment-list">{runs.slice(0, 4).map((item) => <article key={item.run_id}>
            <div className="assessment-list-copy"><small>{item.status_label}</small><h2>{item.title}</h2><p>{item.scenario_name}</p></div>
            <dl><div><dt>Checked</dt><dd>{item.candidates_attempted}/{item.max_budget}</dd></div><div><dt>Time</dt><dd>{item.wall_clock_seconds}s</dd></div></dl>
            <button className="secondary-button" onClick={() => onSelectRun(item.run_id)} aria-label={`Open ${item.title}`}>Open</button>
          </article>)}</div> : <div className="empty-history"><strong>No assessments yet</strong><p>Run the sample or import your migration to get a decision.</p></div>}
        </div>

        <aside className="dashboard-aside">
          <section className="quick-actions-panel">
            <p className="eyebrow">Quick actions</p>
            <button className="quick-action-row" onClick={() => setShowComposer(true)}><span><CodeBracketSquareIcon /></span><div><strong>Prepare a review</strong><small>Describe a risk to check</small></div><ChevronRightIcon /></button>
            <button className="quick-action-row" onClick={onTour}><span><PlayIcon /></span><div><strong>Run the sample</strong><small>See a blocked cutover</small></div><ChevronRightIcon /></button>
          </section>
          <section className="safety-card"><ShieldCheckIcon /><div><strong>Protected by default</strong><p>Sandbox runs. Human approvals.</p></div></section>
        </aside>
      </section>

      {showComposer ? <Modal title="Prepare a review" onClose={() => setShowComposer(false)}>
        <form className="review-composer" onSubmit={submitAgentRequest}>
          <p>Tell CutoverProof what to check. It will prepare a draft for you.</p>
          <label htmlFor="agent-request">What should we check?</label>
          <textarea id="agent-request" aria-label="Ask CutoverProof agent" value={agentPrompt} onChange={(event) => setAgentPrompt(event.target.value)} maxLength={600} />
          <div className="review-examples">
            <button type="button" onClick={() => setAgentPrompt("Check for stale writes during the compatibility window.")}>Stale writes</button>
            <button type="button" onClick={() => setAgentPrompt("Inspect the cutover ordering and prepare a review.")}>Cutover order</button>
          </div>
          {agentActivity.length ? <ol className="review-progress" aria-live="polite">{agentActivity.map((item) => <li key={item.label}><CheckCircleIcon /><span><strong>{item.label}</strong><small>{item.detail}</small></span></li>)}</ol> : null}
          {agentReply ? <div className="review-ready" role="status"><CheckCircleIcon /><div><strong>Draft ready</strong><p>{agentReply}</p></div></div> : null}
          {agentError ? <p className="inline-error" role="alert">{agentError}</p> : null}
          <footer><button type="button" className="secondary-button" onClick={() => setShowComposer(false)}>Close</button><button className="primary-button" disabled={agentBusy}>{agentBusy ? "Preparing…" : "Prepare review"}<ArrowRightIcon /></button></footer>
        </form>
      </Modal> : null}
    </main>
  );
}

function useWebMcpAvailability(active: boolean): WebMcpAvailability {
  const [availability, setAvailability] = useState<WebMcpAvailability>({
    supported: false,
    ready: false,
    toolCount: 0,
    error: null,
  });
  useEffect(() => {
    if (!active) {
      setAvailability({ supported: false, ready: false, toolCount: 0, error: null });
      return;
    }
    const registration = registerCutoverProofTools();
    setAvailability({ supported: registration.supported, ready: false, toolCount: registration.toolNames.length, error: null });
    registration.ready.then(() => {
      setAvailability({ supported: registration.supported, ready: registration.supported, toolCount: registration.toolNames.length, error: null });
    }).catch((reason: unknown) => {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      setAvailability({ supported: registration.supported, ready: false, toolCount: registration.toolNames.length, error: reason instanceof Error ? reason.message : "Browser tool registration failed." });
    });
    return registration.unregister;
  }, [active]);
  return availability;
}

function GuidedDemoModal({
  scenario,
  health,
  onClose,
  onStart,
}: {
  scenario: ScenarioSummary;
  health: Health | null;
  onClose: () => void;
  onStart: (payload: Record<string, unknown>) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const primary = scenario.id === "u1_status_trigger_race";

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onStart({
        scenario_id: scenario.id,
        approach: "specialised_agent",
        budget: primary ? 4 : Math.min(4, scenario.max_candidates),
        seed: 42,
        request_repair: primary,
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The assessment could not start.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Run assessment" onClose={onClose}>
      <form className="guided-demo-form" onSubmit={submit}>
        <section className="demo-intro">
          <span className="demo-mark"><PlayIcon /></span>
          <div>
            <p className="eyebrow">{primary ? "Sample migration" : "Saved migration"}</p>
            <h3>{scenario.name}</h3>
            <p>{scenario.description}</p>
          </div>
        </section>

        <ol className="demo-steps">
          <li><span>01</span><div><strong>Plan dangerous orderings</strong><p>Gemini inspects the declared migration graph and proposes bounded candidate schedules.</p></div></li>
          <li><span>02</span><div><strong>Execute against PostgreSQL</strong><p>Each candidate starts from a clean disposable schema and runs real SQL operations.</p></div></li>
          <li><span>03</span><div><strong>Return usable proof</strong><p>See the exact ordering, invariant, violating row, and human-gated repair replay.</p></div></li>
        </ol>

        <div className="demo-facts">
          <span><small>Candidate budget</small><strong>{primary ? 4 : Math.min(4, scenario.max_candidates)}</strong></span>
          <span><small>Operations</small><strong>{scenario.operation_count}</strong></span>
          <span><small>Invariants</small><strong>{scenario.invariant_count}</strong></span>
          <span><small>Environment</small><strong>Sandbox</strong></span>
        </div>

        <div className="boundary-note"><ShieldCheckIcon /><div><strong>Runs in a clean sandbox</strong><p>CutoverProof resets only its dedicated test database.</p></div></div>
        {!health?.model_configured ? <p className="form-warning">Gemini is not configured on this server.</p> : null}
        {error ? <p className="inline-error">{error}</p> : null}
        <footer>
          <button className="secondary-button" type="button" onClick={onClose}>Cancel</button>
          <button className="primary-button" disabled={busy || !health?.model_configured}>{busy ? "Starting…" : "Run assessment"}</button>
        </footer>
      </form>
    </Modal>
  );
}

const TOUR_STEPS = [
  {
    target: null,
    title: "Find a migration bug",
    body: "Run the sample and see the exact failing row.",
  },
  {
    target: "[data-tour='how-it-works']",
    title: "Review the result",
    body: "CutoverProof shows the decision, failure, and next step.",
  },
  {
    target: "[data-tour='new-assessment']",
    title: "Test your own migration",
    body: "Upload a validated migration pack when you’re ready.",
  },
] as const;

function GuidedTour({ scenario, health, onClose, onStart }: { scenario: ScenarioSummary; health: Health | null; onClose: () => void; onStart: (payload: Record<string, unknown>) => Promise<void> }) {
  const [step, setStep] = useState(0);
  const [rect, setRect] = useState<{ top: number; left: number; width: number; height: number } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cardRef = useRef<HTMLElement>(null);
  const current = TOUR_STEPS[step];

  useEffect(() => {
    const previousOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    return () => { document.documentElement.style.overflow = previousOverflow; };
  }, []);

  useEffect(() => {
    const update = () => {
      if (!current.target) { setRect(null); return; }
      const target = document.querySelector<HTMLElement>(current.target);
      if (!target) { setRect(null); return; }
      target.scrollIntoView({ block: "center", behavior: "auto" });
      const next = target.getBoundingClientRect();
      setRect({ top: next.top, left: next.left, width: next.width, height: next.height });
    };
    update();
    const timer = window.setTimeout(update, 80);
    window.addEventListener("resize", update);
    return () => { window.clearTimeout(timer); window.removeEventListener("resize", update); };
  }, [current.target]);

  useEffect(() => { cardRef.current?.focus(); }, [step]);

  const cardWidth = Math.min(390, window.innerWidth - 32);
  const estimatedHeight = 260;
  const cardStyle = rect ? {
    width: cardWidth,
    left: Math.max(16, Math.min(rect.left, window.innerWidth - cardWidth - 16)),
    top: rect.top + rect.height + estimatedHeight + 24 < window.innerHeight ? rect.top + rect.height + 18 : Math.max(16, rect.top - estimatedHeight - 18),
  } : undefined;
  const spotlightStyle = rect ? { top: rect.top - 8, left: rect.left - 8, width: rect.width + 16, height: rect.height + 16 } : undefined;

  const runDemo = async () => {
    setBusy(true);
    setError(null);
    try {
      await onStart({ scenario_id: scenario.id, approach: "specialised_agent", budget: 4, seed: 42, request_repair: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The demo could not start.");
      setBusy(false);
    }
  };

  return <div className={`tour-layer ${rect ? "has-target" : "centered"}`} role="dialog" aria-modal="true" aria-label="Guided tour">
    {rect ? <div className="tour-spotlight" style={spotlightStyle} /> : <div className="tour-scrim" />}
    <section className="tour-card" style={cardStyle} ref={cardRef} tabIndex={-1}>
      <div className="tour-card-head"><span>{step + 1} of {TOUR_STEPS.length}</span><button className="icon-button" aria-label="Exit tour" onClick={onClose}><XMarkIcon /></button></div>
      <h2>{current.title}</h2>
      <p>{current.body}</p>
      {step === 0 ? <div className="tour-sample"><small>Sample</small><strong>{scenario.name}</strong></div> : null}
      {error ? <p className="inline-error" role="alert">{error}</p> : null}
      <footer>
        <button className="secondary-button" onClick={step === 0 ? onClose : () => setStep((value) => value - 1)}>{step === 0 ? "Skip" : "Back"}</button>
        {step < TOUR_STEPS.length - 1 ? <button className="primary-button" onClick={() => setStep((value) => value + 1)}>{step === 0 ? "Start tour" : "Next"}<ChevronRightIcon /></button> : <button className="primary-button" disabled={busy || !health?.model_configured} onClick={() => void runDemo()}>{busy ? "Starting…" : "Run sample"}<PlayIcon /></button>}
      </footer>
    </section>
  </div>;
}

function CustomAssessmentModal({
  health,
  defaultBudget,
  onClose,
  onImportAndStart,
}: {
  health: Health | null;
  defaultBudget: number;
  onClose: () => void;
  onImportAndStart: (pack: unknown, budget: number) => Promise<void>;
}) {
  const [jsonText, setJsonText] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const packSummary = useMemo(() => {
    if (!jsonText.trim()) return null;
    try {
      const pack = JSON.parse(jsonText) as { name?: unknown; operations?: unknown; invariants?: unknown };
      if (typeof pack.name !== "string" || !pack.name.trim() || !pack.operations || typeof pack.operations !== "object" || !Array.isArray(pack.invariants)) return null;
      return { name: pack.name, operations: Object.keys(pack.operations).length, invariants: pack.invariants.length };
    } catch {
      return null;
    }
  }, [jsonText]);

  const loadTemplate = async () => {
    const template = await apiRequest<unknown>("/api/scenario-packs/template");
    setJsonText(JSON.stringify(template, null, 2));
    setSourceName("Example template");
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onImportAndStart(JSON.parse(jsonText), defaultBudget);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The assessment could not start.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="New assessment" onClose={onClose}>
      <form className="assessment-form custom-assessment-form" onSubmit={submit}>
        <div className="custom-intro">
          <span className="custom-intro-icon"><ArrowUpTrayIcon /></span>
          <div><h3>Choose a migration pack</h3><p>Upload JSON or start from the sample.</p></div>
        </div>
        <div className="import-actions">
          <button className="secondary-button" type="button" onClick={() => fileRef.current?.click()}><ArrowUpTrayIcon />Choose JSON file</button>
          <button className="secondary-button" type="button" onClick={() => void loadTemplate()}>Use sample pack</button>
          <input ref={fileRef} hidden type="file" accept="application/json" onChange={(event) => { const file = event.target.files?.[0]; if (file) void file.text().then((text) => { setJsonText(text); setSourceName(file.name); }); }} />
        </div>
        {packSummary ? <div className="assessment-ready"><CheckCircleIcon /><span><strong>{packSummary.name}</strong><small>{packSummary.operations} steps · {packSummary.invariants} check{packSummary.invariants === 1 ? "" : "s"} · {sourceName}</small></span></div> : jsonText ? <p className="inline-error" role="alert">This file is not a valid migration pack.</p> : <p className="assessment-choice-copy">No file selected.</p>}
        {jsonText ? <details className="configuration-details"><summary>Review JSON</summary><label className="configuration-editor"><span>Migration configuration <small>{sourceName}</small></span><textarea value={jsonText} onChange={(event) => setJsonText(event.target.value)} required /></label></details> : null}
        <div className="boundary-note"><ShieldCheckIcon /><div><strong>Sandbox only</strong><p>Production targets and unsafe SQL are refused.</p></div></div>
        {!health?.model_configured ? <p className="form-warning">Risk planning is offline.</p> : null}
        {error ? <p className="inline-error">{error}</p> : null}
        <footer><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={busy || !health?.model_configured || !packSummary}>{busy ? "Starting…" : "Run assessment"}</button></footer>
      </form>
    </Modal>
  );
}

export function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  useEffect(() => {
    apiRequest<Session>("/api/auth/session").then(setSession).finally(() => setSessionLoading(false));
  }, []);
  useEffect(() => {
    setCsrfToken(session?.csrf_token);
  }, [session?.csrf_token]);

  const active = Boolean(session?.authenticated);
  const data = useWorkspaceData(active);
  const webMcp = useWebMcpAvailability(active);
  const [view, setView] = useState<View>("overview");
  const [run, setRun] = useState<RunDetail | null>(null);
  const [guidedScenarioId, setGuidedScenarioId] = useState("u1_status_trigger_race");
  const [showTour, setShowTour] = useState(false);
  const [showGuided, setShowGuided] = useState(false);
  const [showCustom, setShowCustom] = useState(false);
  const [showApproval, setShowApproval] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const [job, setJob] = useState<JobState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedConnection, setSelectedConnection] = useState<ConnectionSummary | null>(null);
  const [reviewDrafts, setReviewDrafts] = useState<ChangeReviewDraft[]>([]);
  const [preferences, setPreferences] = useState<AppPreferences>(() => {
    try {
      const saved = window.localStorage.getItem("cutoverproof:preferences");
      return saved ? { ...DEFAULT_PREFERENCES, ...(JSON.parse(saved) as Partial<AppPreferences>) } : DEFAULT_PREFERENCES;
    } catch {
      return DEFAULT_PREFERENCES;
    }
  });
  const [userRunIds, setUserRunIds] = useState<string[]>(() => {
    try {
      const saved = window.sessionStorage.getItem("cutoverproof:user-run-ids");
      return saved ? (JSON.parse(saved) as string[]) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    window.sessionStorage.setItem("cutoverproof:user-run-ids", JSON.stringify(userRunIds));
  }, [userRunIds]);

  const refreshReviewDrafts = useCallback(async () => {
    if (!active) return;
    try {
      setReviewDrafts(await apiRequest<ChangeReviewDraft[]>("/api/webmcp/review-drafts"));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Agent-prepared reviews could not load.");
    }
  }, [active]);

  const handleDraftPrepared = useCallback((draft: ChangeReviewDraft) => {
    setReviewDrafts((current) => [draft, ...current.filter((item) => item.id !== draft.id)]);
  }, []);

  useEffect(() => {
    if (active) void refreshReviewDrafts();
    else setReviewDrafts([]);
  }, [active, refreshReviewDrafts]);

  useEffect(() => {
    const handleReviewCreated = (event: Event) => {
      const draft = (event as CustomEvent<ChangeReviewDraft>).detail;
      if (!draft) return;
      handleDraftPrepared(draft);
      setView("overview");
    };
    window.addEventListener(WEBMCP_REVIEW_CREATED, handleReviewCreated);
    return () => window.removeEventListener(WEBMCP_REVIEW_CREATED, handleReviewCreated);
  }, [handleDraftPrepared]);

  const savePreferences = useCallback((next: AppPreferences) => {
    setPreferences(next);
    window.localStorage.setItem("cutoverproof:preferences", JSON.stringify(next));
  }, []);

  const openGuided = (scenarioId = "u1_status_trigger_race") => {
    setGuidedScenarioId(scenarioId);
    setShowGuided(true);
  };

  const openTour = () => {
    setGuidedScenarioId("u1_status_trigger_race");
    setView("overview");
    setShowTour(true);
  };

  const selectRun = useCallback(async (id: string) => {
    try {
      setRun(await apiRequest<RunDetail>(`/api/runs/${id}`));
      setView("assessment");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Run could not load.");
    }
  }, []);

  useEffect(() => {
    const handleOpenRepair = (event: Event) => {
      const runId = (event as CustomEvent<{ run_id: string }>).detail?.run_id;
      if (!runId) return;
      void apiRequest<RunDetail>(`/api/runs/${encodeURIComponent(runId)}`).then((detail) => {
        setRun(detail);
        setView("assessment");
        setShowEvidence(false);
        setShowCustom(false);
        setShowGuided(false);
        setShowTour(false);
        setShowApproval(Boolean(detail.repair && !detail.repair.approved));
      }).catch((reason) => {
        setError(reason instanceof Error ? reason.message : "Repair review could not open.");
      });
    };
    window.addEventListener(WEBMCP_OPEN_REPAIR, handleOpenRepair);
    return () => window.removeEventListener(WEBMCP_OPEN_REPAIR, handleOpenRepair);
  }, []);

  const startAssessment = useCallback(async (payload: Record<string, unknown>) => {
    const accepted = await apiRequest<{ job_id: string; status: "queued" }>("/api/runs", {
      method: "POST",
      body: JSON.stringify({
        ...payload,
        connection_id: selectedConnection && selectedConnection.id !== "configured" ? selectedConnection.id : null,
      }),
    });
    setJob({ ...accepted, progress: 0 });
    setShowTour(false);
    setShowGuided(false);
    setShowCustom(false);
  }, [selectedConnection]);

  const importAndStart = useCallback(async (pack: unknown, budget: number) => {
    const imported = await apiRequest<{ id: string }>("/api/scenario-packs", { method: "POST", body: JSON.stringify(pack) });
    await data.refreshScenarios();
    await startAssessment({ scenario_id: imported.id, approach: "specialised_agent", budget, seed: 42, request_repair: true });
  }, [data.refreshScenarios, startAssessment]);

  useEffect(() => {
    if (!job || ["completed", "failed"].includes(job.status)) return;
    const timer = window.setInterval(() => {
      apiRequest<JobState>(`/api/jobs/${job.job_id}`).then((next) => {
        setJob(next);
        if (next.status === "completed" && next.result) {
          setRun(next.result);
          setUserRunIds((current) => current.includes(next.result!.run_id) ? current : [...current, next.result!.run_id]);
          setView("assessment");
          if (preferences.autoOpenEvidence) setShowEvidence(true);
          void data.refreshRuns();
        }
      }).catch((reason) => setJob({
        ...job,
        status: "failed",
        progress: 100,
        error: reason instanceof Error ? reason.message : "Job polling failed.",
      }));
    }, 900);
    return () => window.clearInterval(timer);
  }, [job, data.refreshRuns, preferences.autoOpenEvidence]);

  const logout = async () => {
    await apiRequest("/api/auth/logout", { method: "POST" });
    setSession({ authenticated: false, email: null });
    setRun(null);
    setUserRunIds([]);
    setReviewDrafts([]);
    window.sessionStorage.removeItem("cutoverproof:user-run-ids");
    setView("overview");
  };

  const approve = async (name: string) => {
    if (!run) return;
    try {
      const approved = await apiRequest<RunDetail>(`/api/runs/${run.run_id}/approve-repair`, {
        method: "POST",
        body: JSON.stringify({ reviewer_name: name }),
      });
      setRun(approved);
      setShowApproval(false);
      await data.refreshRuns();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Replay failed.");
    }
  };

  const guidedScenario = data.scenarios.find((item) => item.id === guidedScenarioId) ?? data.scenarios[0];
  const userRuns = data.runs.filter((item) => userRunIds.includes(item.run_id));
  const latestDraft = reviewDrafts[0] ?? null;

  const content = useMemo(() => {
    if (data.initializing) return <main className="main-content"><div className="loading-panel">Opening workspace…</div></main>;
    if (view === "overview") return <ProductOverview onTour={openTour} onNewAssessment={() => setShowCustom(true)} onDraftPrepared={handleDraftPrepared} onReviewDraft={openGuided} onSelectRun={selectRun} latestDraft={latestDraft} runs={userRuns} />;
    if (view === "assessments") return <AssessmentHistoryView runs={userRuns} onNew={() => setShowCustom(true)} onSelect={selectRun} />;
    if (view === "settings") return <SettingsView email={session?.email ?? ""} health={data.health} connection={data.connections?.configured ?? null} webMcp={webMcp} preferences={preferences} onSave={savePreferences} onLogout={() => void logout()} />;
    if (view === "connections") return <ConnectionsView data={data.connections} onRefresh={data.refreshConnections} onSelect={setSelectedConnection} />;
    if (run) return <AssessmentView run={run} onApprove={() => setShowApproval(true)} onEvidence={() => setShowEvidence(true)} onRetry={() => openGuided(run.scenario_id)} />;
    return <ProductOverview onTour={openTour} onNewAssessment={() => setShowCustom(true)} onDraftPrepared={handleDraftPrepared} onReviewDraft={openGuided} onSelectRun={selectRun} latestDraft={latestDraft} runs={userRuns} />;
  }, [data, view, run, selectRun, userRuns, session?.email, preferences, savePreferences, latestDraft, webMcp, handleDraftPrepared]);

  if (sessionLoading) return <div className="login-loading"><ShieldCheckIcon />CutoverProof</div>;
  if (!session?.authenticated) return <LoginView onSignedIn={setSession} />;

  return (
    <AppShell view={view} email={session.email ?? "engineer@cutoverproof.dev"} onView={setView} onNew={() => setShowCustom(true)} onLogout={() => void logout()}>
      {error ? <div className="error-toast"><ExclamationTriangleIcon /><span>{error}</span><button onClick={() => setError(null)}><XMarkIcon /></button></div> : null}
      {job && job.status !== "completed" ? <JobBanner job={job} /> : null}
      {content}
      {showTour && guidedScenario ? <GuidedTour scenario={guidedScenario} health={data.health} onClose={() => setShowTour(false)} onStart={startAssessment} /> : null}
      {showGuided && guidedScenario ? <GuidedDemoModal scenario={guidedScenario} health={data.health} onClose={() => setShowGuided(false)} onStart={startAssessment} /> : null}
      {showCustom ? <CustomAssessmentModal health={data.health} defaultBudget={preferences.candidateBudget} onClose={() => setShowCustom(false)} onImportAndStart={importAndStart} /> : null}
      {showApproval && run ? <ApprovalModal run={run} onClose={() => setShowApproval(false)} onApprove={approve} /> : null}
      {showEvidence && run ? <EvidenceModal run={run} onClose={() => setShowEvidence(false)} /> : null}
    </AppShell>
  );
}
