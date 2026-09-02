import {
  ArrowPathIcon, ArrowRightIcon, ArrowUpTrayIcon, CheckCircleIcon, CheckIcon, Cog6ToothIcon,
  ChevronDownIcon, ChevronRightIcon, CircleStackIcon, ClockIcon, CodeBracketSquareIcon,
  ExclamationTriangleIcon, HomeIcon, InformationCircleIcon, LockClosedIcon, PlayIcon, PlusIcon,
  QueueListIcon, ShieldCheckIcon, UserCircleIcon, XMarkIcon,
} from "@heroicons/react/24/outline";
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
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

function OverviewView({ runs, scenarios, health, onNew, onCatalog, onConnections, onSelectRun }: { runs: RunSummary[]; scenarios: ScenarioSummary[]; health: Health | null; onNew: () => void; onCatalog: () => void; onConnections: () => void; onSelectRun: (id: string) => void }) {
  return <main className="main-content overview-view"><section className="welcome-row"><div><p className="eyebrow">Migration safety workspace</p><h1>Prove the cutover path before production.</h1><p className="lede">Choose a realistic migration pack or import your own schema, operations, and invariant. CutoverProof searches dangerous orderings and executes each candidate from a clean PostgreSQL reset.</p></div><button className="primary-button hero-cta" onClick={onNew}><PlayIcon />Run guided demo</button></section><section className="start-grid"><button className="action-card featured" onClick={onNew}><span className="card-icon"><PlayIcon /></span><span><small>Fastest path</small><strong>Run guided demo</strong><p>Test the status-normalization race and watch the agent find an executed counterexample.</p></span><ChevronRightIcon /></button><button className="action-card" onClick={onCatalog}><span className="card-icon"><CodeBracketSquareIcon /></span><span><small>Bring your migration</small><strong>Import assessment pack</strong><p>Supply schema SQL, seed data, declared operations, and a queryable invariant.</p></span><ChevronRightIcon /></button><button className="action-card" onClick={onConnections}><span className="card-icon"><CircleStackIcon /></span><span><small>Execution target</small><strong>Verify PostgreSQL sandbox</strong><p>Inspect the configured target or test an exact allow-listed disposable database.</p></span><ChevronRightIcon /></button></section><section className="overview-columns"><div><div className="section-heading"><div><p className="eyebrow">Recent evidence</p><h2>Latest assessment runs</h2></div><button className="text-button" onClick={onCatalog}>View packs <ArrowRightIcon /></button></div><div className="recent-list">{runs.length ? runs.slice(0, 4).map((run) => <button key={run.run_id} onClick={() => onSelectRun(run.run_id)}><span className={`run-indicator ${run.status}`} /><span><strong>{run.scenario_name}</strong><small>{run.candidates_attempted}/{run.max_budget} candidates · {run.wall_clock_seconds}s</small></span><span className={`table-status ${run.status}`}>{run.status_label}</span><ChevronRightIcon /></button>) : <div className="empty-inline">No runs yet. Start with the guided demo.</div>}</div></div><aside className="system-card"><p className="eyebrow">Ready to run</p><h2>Execution services</h2><dl><div><dt><CircleStackIcon />PostgreSQL sandbox</dt><dd><span className="status-dot" />Configured</dd></div><div><dt><ShieldCheckIcon />Gemini planner</dt><dd><span className={`status-dot ${health?.model_configured ? "" : "warning"}`} />{health?.model_configured ? "Configured" : "Needs key"}</dd></div><div><dt><CodeBracketSquareIcon />Available packs</dt><dd>{scenarios.length}</dd></div></dl><p>Every candidate resets the disposable schema. No production database is accepted.</p></aside></section></main>;
}

function AssessmentsView({ scenarios, onRun, onImport }: { scenarios: ScenarioSummary[]; onRun: (id: string) => void; onImport: () => void }) {
  const visibleScenarios = scenarios.filter((scenario) => !["s1_compat_first_safe", "s2_compat_read_safe"].includes(scenario.id));
  return <main className="main-content list-view assessment-library"><div className="simple-page-heading"><div><h1>Assessments</h1><p>Run a saved migration test or import your own.</p></div><button className="primary-button" onClick={onImport}><PlusIcon />New assessment</button></div><div className="assessment-list">{visibleScenarios.map((scenario) => <article key={scenario.id}><div className="assessment-list-copy"><small>{scenario.id.startsWith("u") ? "Sample" : "Imported"}</small><h2>{scenario.name}</h2><p>{scenario.description}</p></div><dl><div><dt>Steps</dt><dd>{scenario.operation_count}</dd></div><div><dt>Checks</dt><dd>{scenario.invariant_count}</dd></div></dl><button className="secondary-button" onClick={() => onRun(scenario.id)}><PlayIcon />Run</button></article>)}</div></main>;
}

function RunsView({ runs, onSelect }: { runs: RunSummary[]; onSelect: (runId: string) => void }) { const customerRuns = runs.filter((item) => !["s1_compat_first_safe", "s2_compat_read_safe"].includes(item.scenario_id)); return <main className="main-content list-view"><div className="simple-page-heading"><div><h1>Runs</h1><p>Open any assessment to review its decision and evidence.</p></div></div><div className="run-table"><div className="table-row table-head"><span>Assessment</span><span>Decision</span><span>Search effort</span><span /></div>{customerRuns.map((item) => <div className="table-row" key={item.run_id}><span><strong>{item.scenario_name}</strong><small>{item.run_id}</small></span><span className={`table-status ${item.status}`}>{item.status_label}</span><span>{item.candidates_attempted}/{item.max_budget} candidates</span><button onClick={() => onSelect(item.run_id)}>Open <ChevronRightIcon /></button></div>)}</div></main>; }

function AssessmentHistoryView({ runs, onNew, onSelect }: { runs: RunSummary[]; onNew: () => void; onSelect: (runId: string) => void }) {
  if (!runs.length) return <main className="main-content list-view assessment-history"><div className="simple-page-heading"><div><h1>Assessments</h1><p>Your completed migration checks will appear here.</p></div></div><section className="assessment-empty"><span><ShieldCheckIcon /></span><h2>No assessments yet</h2><p>Run your first assessment to see its decision and evidence here.</p><button className="primary-button" onClick={onNew}><PlusIcon />New assessment</button></section></main>;
  return <main className="main-content list-view assessment-history"><div className="simple-page-heading"><div><h1>Assessments</h1><p>Review the result and evidence from each migration check.</p></div></div><div className="run-table"><div className="table-row table-head"><span>Assessment</span><span>Decision</span><span>Search effort</span><span /></div>{runs.map((item) => <div className="table-row" key={item.run_id}><span><strong>{item.scenario_name}</strong><small>{item.run_id}</small></span><span className={`table-status ${item.status}`}>{item.status_label}</span><span>{item.candidates_attempted}/{item.max_budget} candidates</span><button onClick={() => onSelect(item.run_id)}>Open <ChevronRightIcon /></button></div>)}</div></main>;
}

function SettingsView({
  email,
  health,
  connection,
  preferences,
  onSave,
  onLogout,
}: {
  email: string;
  health: Health | null;
  connection: ConnectionSummary | null;
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
      <div><h1>Settings</h1><p>Choose how new assessments run and review the safeguards that cannot be changed.</p></div>
      <button className="primary-button settings-save" disabled={!dirty} onClick={save}><CheckIcon />{saved ? "Saved" : "Save changes"}</button>
    </div>

    <div className="settings-layout">
      <div className="settings-main">
        <section className="settings-section settings-preferences">
          <div className="settings-section-heading"><span className="settings-icon"><Cog6ToothIcon /></span><div><h2>Assessment defaults</h2><p>These defaults apply when you import a new migration.</p></div></div>
          <div className="settings-control-row">
            <label htmlFor="candidate-budget"><strong>Candidate budget</strong><span>Maximum operation orderings tested per assessment.</span></label>
            <select id="candidate-budget" value={draft.candidateBudget} onChange={(event) => setDraft((current) => ({ ...current, candidateBudget: Number(event.target.value) }))}>
              {[2, 4, 6, 8].map((value) => <option key={value} value={value}>{value} candidates</option>)}
            </select>
          </div>
          <div className="settings-control-row">
            <div><strong>Open technical evidence automatically</strong><span>Show the executed ordering and violating rows as soon as a run finishes.</span></div>
            <button type="button" role="switch" aria-checked={draft.autoOpenEvidence} aria-label="Open technical evidence automatically" className={`toggle-control ${draft.autoOpenEvidence ? "on" : ""}`} onClick={() => setDraft((current) => ({ ...current, autoOpenEvidence: !current.autoOpenEvidence }))}><span /></button>
          </div>
          <footer className="settings-section-footer"><button className="text-button" onClick={reset}><ArrowPathIcon />Reset defaults</button>{saved ? <span className="saved-note"><CheckCircleIcon />Preferences saved</span> : null}</footer>
        </section>

        <section className="settings-section">
          <div className="settings-section-heading"><span className="settings-icon safe"><ShieldCheckIcon /></span><div><h2>Safety boundaries</h2><p>Permanent controls that protect real databases and consequential actions.</p></div></div>
          <dl className="settings-status-list">
            <div><dt><strong>Execution target</strong><span>Every candidate begins from a clean schema.</span></dt><dd><span className="status-dot" />Disposable PostgreSQL</dd></div>
            <div><dt><strong>Production access</strong><span>Production-shaped hosts and database identities are refused.</span></dt><dd><LockClosedIcon />Blocked</dd></div>
            <div><dt><strong>Repair execution</strong><span>A proposed repair cannot run until a person approves it.</span></dt><dd><UserCircleIcon />Human approval</dd></div>
          </dl>
        </section>
      </div>

      <aside className="settings-aside">
        <section className="settings-section runtime-card">
          <div className="settings-section-heading"><span className="settings-icon"><CircleStackIcon /></span><div><h2>Runtime status</h2><p>Services used by new assessments.</p></div></div>
          <dl className="runtime-list">
            <div><dt>PostgreSQL sandbox</dt><dd><span className="status-dot" />{connection ? "Available" : "Checking"}</dd></div>
            <div><dt>Gemini planner</dt><dd><span className={`status-dot ${health?.model_configured ? "" : "warning"}`} />{health?.model_configured ? "Ready" : "Not configured"}</dd></div>
            <div><dt>Execution boundary</dt><dd>{health?.execution_boundary ?? "Loading"}</dd></div>
          </dl>
        </section>

        <section className="settings-section account-card">
          <div className="settings-section-heading"><span className="settings-icon neutral"><UserCircleIcon /></span><div><h2>Account</h2><p>Your current CutoverProof session.</p></div></div>
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

function PhaseRail({ run }: { run: RunDetail }) { const phases = run.phases.slice(0, 5); const conflict = run.status === "blocked" || run.status === "repair_failed"; return <div className="phase-rail" aria-label="Migration phase timeline">{phases.map((phase, index) => <div className="phase-group" key={phase.id}><div className="phase-item"><span className="phase-name">{phase.name}</span><span className={`phase-node ${phase.state}`}>{phase.state === "complete" ? <CheckIcon /> : <ClockIcon />}</span></div>{index < phases.length - 1 ? <span className={`phase-connector ${phase.id === "backfill" && conflict ? "conflict" : ""}`} /> : null}{phase.id === "backfill" && conflict ? <div className="conflict-marker" aria-label="Conflict: legacy write after backfill"><span className="conflict-node"><XMarkIcon /></span><i className="conflict-stem" /><b className="conflict-label">Legacy write after backfill</b></div> : null}</div>)}</div>; }

function AssessmentView({ run, onApprove, onEvidence, onRetry }: { run: RunDetail; onApprove: () => void; onEvidence: () => void; onRetry: () => void }) {
  const blocked = run.status === "blocked" || run.status === "repair_failed";
  const replayed = Boolean(run.replay);
  const failed = run.status === "failed";
  const inconclusive = run.status === "inconclusive";
  const recommendationTitle = failed ? "Retry the assessment" : run.repair?.name ?? "Review the failing ordering";
  const recommendationCopy = failed
    ? "No migration decision was made. Retry the same pack; if it stops again, inspect the technical error before changing any migration SQL."
    : run.repair?.description ?? "Inspect the exact executed steps and violating rows before changing the migration plan.";
  return <main className="main-content assessment-view"><div className="breadcrumbs"><span>Assessments</span><ChevronRightIcon /><strong>{run.title}</strong></div><section className="assessment-heading"><div><p className="eyebrow">Executed safety assessment</p><h1>{run.title}</h1><p className="lede">{replayed ? "The approved repair passed the identical failing schedule in the disposable sandbox." : failed ? "The run stopped before a migration decision could be produced. This is not a verdict on the migration." : inconclusive ? "No counterexample was found within this bounded search. This is evidence, not proof of safety." : "An executed ordering violated the declared database invariant. Review the finding before cutover."}</p></div><div className={`verdict ${blocked ? "danger" : failed ? "failed" : inconclusive ? "caution" : "verified"}`}>{blocked || failed ? <XMarkIcon /> : inconclusive ? <ClockIcon /> : <ShieldCheckIcon />}<span>{run.status_label}</span></div></section><section className="decision-grid"><div className="finding-column"><p className="section-label">Plain-language finding</p><div className="finding-statement"><span className="finding-icon"><ExclamationTriangleIcon /></span><p>{run.finding}</p></div><div className="phase-section"><p className="section-label">Migration phases and conflict</p><PhaseRail run={run} /></div></div><aside className="recommendation"><p className="section-label">{replayed ? "Verified action" : "Recommended action"}</p><h2>{recommendationTitle}</h2><p>{recommendationCopy}</p>{failed ? <button className="primary-button approve-button" onClick={onRetry}><PlayIcon />Retry assessment</button> : run.repair ? <button className="primary-button approve-button" onClick={onApprove} disabled={replayed}><ShieldCheckIcon />{replayed ? "Repair replay verified" : "Review & approve repair"}</button> : null}<button className="link-button" onClick={onEvidence}>Inspect technical evidence <ChevronRightIcon /></button></aside></section><footer className="run-summary"><span><InformationCircleIcon />{run.candidates_attempted} of {run.max_budget} candidates executed</span><i /><span><ClockIcon />{replayed ? `Replay passed in ${run.replay?.duration_ms} ms` : `${run.wall_clock_seconds}s total runtime`}</span></footer></main>;
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) { useEffect(() => { const key = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); }; window.addEventListener("keydown", key); return () => window.removeEventListener("keydown", key); }, [onClose]); return <div className="modal-backdrop" onMouseDown={onClose}><section className="modal" role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}><header><h2>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={onClose}><XMarkIcon /></button></header>{children}</section></div>; }

function NewAssessmentModal({ scenarios, initialScenario, mode: initialMode, health, onClose, onStart, onImportAndStart }: { scenarios: ScenarioSummary[]; initialScenario?: string; mode: "guided" | "custom"; health: Health | null; onClose: () => void; onStart: (payload: Record<string, unknown>) => Promise<void>; onImportAndStart: (pack: unknown, budget: number) => Promise<void> }) { const [mode, setMode] = useState(initialMode); const [scenarioId, setScenarioId] = useState(initialScenario ?? scenarios[0]?.id ?? ""); const [budget, setBudget] = useState(4); const [jsonText, setJsonText] = useState(""); const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null); const fileRef = useRef<HTMLInputElement>(null); const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(null); try { if (mode === "guided") await onStart({ scenario_id: scenarioId, approach: "specialised_agent", budget, seed: 42, request_repair: true }); else await onImportAndStart(JSON.parse(jsonText), budget); } catch (reason) { setError(reason instanceof Error ? reason.message : "The assessment could not start."); } finally { setBusy(false); } }; const loadTemplate = async () => setJsonText(JSON.stringify(await apiRequest<unknown>("/api/scenario-packs/template"), null, 2)); return <Modal title="New safety assessment" onClose={onClose}><form className="assessment-form" onSubmit={submit}><div className="mode-switch"><button type="button" className={mode === "guided" ? "active" : ""} onClick={() => setMode("guided")}><PlayIcon />Guided demo</button><button type="button" className={mode === "custom" ? "active" : ""} onClick={() => setMode("custom")}><ArrowUpTrayIcon />Custom pack</button></div>{mode === "guided" ? <><label>Migration assessment pack<select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>{scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}</select></label><p className="scenario-description">{scenarios.find((scenario) => scenario.id === scenarioId)?.description}</p></> : <><div className="import-actions"><button className="secondary-button" type="button" onClick={() => void loadTemplate()}>Load example template</button><button className="secondary-button" type="button" onClick={() => fileRef.current?.click()}><ArrowUpTrayIcon />Choose JSON file</button><input ref={fileRef} hidden type="file" accept="application/json" onChange={(event) => { const file = event.target.files?.[0]; if (file) void file.text().then(setJsonText); }} /></div><label>Assessment pack JSON<textarea value={jsonText} onChange={(event) => setJsonText(event.target.value)} placeholder="Load the example, then replace it with your schema, operations, and invariant." required /></label><p className="boundary-copy">The pack is validated before it can run. Server-level SQL, filesystem access, role changes, and database creation are rejected.</p></>}<label>Candidate budget<input type="number" min="1" max="8" value={budget} onChange={(event) => setBudget(Number(event.target.value))} /></label><div className="boundary-note"><ShieldCheckIcon /><div><strong>Clean, disposable execution</strong><p>Every candidate starts from the pack’s schema and seed SQL. Production-shaped databases are refused by identity and host allowlist.</p></div></div>{!health?.model_configured ? <p className="form-warning">Gemini is not configured on this server.</p> : null}{error ? <p className="inline-error">{error}</p> : null}<footer><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={busy || !health?.model_configured || (mode === "guided" && !scenarioId)}>{busy ? "Starting…" : mode === "custom" ? "Import & run assessment" : "Run safety assessment"}</button></footer></form></Modal>; }

function EvidenceModal({ run, onClose }: { run: RunDetail; onClose: () => void }) { const columns = Array.from(new Set(run.evidence_rows.flatMap(Object.keys))); const checkName = (run.boundary ?? "No violation").replaceAll("_", " ").replace(/\binvariant\b/gi, "").trim(); return <Modal title="Why CutoverProof blocked this migration" onClose={onClose}><div className="evidence-review"><p className="evidence-intro">This is the exact operation ordering executed in PostgreSQL and the row returned by your invariant—not a model-generated verdict.</p><div className="evidence-meta"><span><strong>Failed check</strong>{checkName}</span><span><strong>Runtime</strong>{run.wall_clock_seconds}s</span><span><strong>Candidates tested</strong>{run.candidates_attempted} of {run.max_budget}</span></div><section><p className="section-label">Executed ordering</p>{run.steps.length ? <ol className="trace-list">{run.steps.map((step) => <li key={`${step.index}-${step.id}`}><span>{step.index}</span><div><strong>{step.description}</strong><small>{step.actor} · {step.phase} · {step.duration_ms}ms</small></div><CheckIcon /></li>)}</ol> : <p className="empty-evidence">No failing ordering was recorded.</p>}</section>{run.evidence_rows.length ? <section><p className="section-label">Database rows that broke the check</p><div className="evidence-table"><div className="evidence-row evidence-head" style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(120px,1fr))` }}>{columns.map((column) => <span key={column}>{column.replaceAll("_", " ")}</span>)}</div>{run.evidence_rows.map((row, index) => <div className="evidence-row" key={index} style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(120px,1fr))` }}>{columns.map((column) => <span key={column}>{String(row[column] ?? "—")}</span>)}</div>)}</div></section> : null}<aside className="audit-callout"><InformationCircleIcon /><div><strong>Need the complete execution record?</strong><p>The detailed timeline includes every SQL step, model/runtime metadata, violating rows, and the repaired replay when approved.</p></div></aside><footer><button className="secondary-button" onClick={() => window.open(run.evidence_url, "_blank", "noopener,noreferrer")}>Open detailed timeline</button><button className="primary-button" onClick={onClose}>Done</button></footer></div></Modal>; }

function ApprovalModal({ run, onClose, onApprove }: { run: RunDetail; onClose: () => void; onApprove: (name: string) => Promise<void> }) { const [name, setName] = useState(""); const [busy, setBusy] = useState(false); return <Modal title="Review bounded repair" onClose={onClose}><form className="approval-form" onSubmit={(event) => { event.preventDefault(); setBusy(true); void onApprove(name).finally(() => setBusy(false)); }}><div className="repair-review"><p className="section-label">Proposed repair</p><h3>{run.repair?.name}</h3><p>{run.repair?.description}</p></div><ul className="safety-list"><li><CheckIcon />Sandbox database only</li><li><CheckIcon />Allow-listed repair SQL</li><li><CheckIcon />Exact failing schedule replay</li></ul><label>Human reviewer<input value={name} minLength={2} required onChange={(event) => setName(event.target.value)} placeholder="Your name" /></label><footer><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={busy}>{busy ? "Replaying…" : "Approve repair & replay"}</button></footer></form></Modal>; }
function JobBanner({ job }: { job: JobState }) { const stages = ["Validate", "Plan", "Execute", "Verify", "Evidence"]; const activeIndex = job.progress < 24 ? 0 : job.progress < 40 ? 1 : job.progress < 72 ? 2 : job.progress < 88 ? 3 : 4; return <div className={`job-banner ${job.status}`} role="status" aria-live="polite"><header><span className="spinner" /><div><strong>{job.status === "failed" ? "Assessment stopped" : "Testing your migration"}</strong><p>{job.error ?? job.stage ?? "Starting the assessment"}</p></div><span>{job.progress}%</span></header><div className="job-progress-track"><i style={{ width: `${job.progress}%` }} /></div><ol>{stages.map((stage, index) => <li className={index < activeIndex ? "complete" : index === activeIndex ? "active" : ""} key={stage}><span>{index < activeIndex ? <CheckIcon /> : index + 1}</span>{stage}</li>)}</ol></div>; }

export function App() {
  const [session, setSession] = useState<Session | null>(null); const [sessionLoading, setSessionLoading] = useState(true); useEffect(() => { apiRequest<Session>("/api/auth/session").then(setSession).finally(() => setSessionLoading(false)); }, []);
  const active = Boolean(session?.authenticated); const data = useWorkspaceData(active); const [view, setView] = useState<View>("overview"); const [run, setRun] = useState<RunDetail | null>(null); const [showNew, setShowNew] = useState(false); const [newMode, setNewMode] = useState<"guided" | "custom">("guided"); const [initialScenario, setInitialScenario] = useState<string | undefined>(); const [showApproval, setShowApproval] = useState(false); const [showEvidence, setShowEvidence] = useState(false); const [job, setJob] = useState<JobState | null>(null); const [error, setError] = useState<string | null>(null); const [selectedConnection, setSelectedConnection] = useState<ConnectionSummary | null>(null);
  const openNew = (mode: "guided" | "custom" = "guided", scenario?: string) => { setNewMode(mode); setInitialScenario(scenario); setShowNew(true); }; const selectRun = useCallback(async (id: string) => { try { setRun(await apiRequest<RunDetail>(`/api/runs/${id}`)); setView("assessment"); } catch (reason) { setError(reason instanceof Error ? reason.message : "Run could not load."); } }, []);
  const startAssessment = useCallback(async (payload: Record<string, unknown>) => { const accepted = await apiRequest<{ job_id: string; status: "queued" }>("/api/runs", { method: "POST", body: JSON.stringify({ ...payload, connection_id: selectedConnection && selectedConnection.id !== "configured" ? selectedConnection.id : null }) }); setJob({ ...accepted, progress: 0 }); setShowNew(false); }, [selectedConnection]);
  const importAndStart = useCallback(async (pack: unknown, budget: number) => { const imported = await apiRequest<{ id: string }>("/api/scenario-packs", { method: "POST", body: JSON.stringify(pack) }); await data.refreshScenarios(); await startAssessment({ scenario_id: imported.id, approach: "specialised_agent", budget, seed: 42, request_repair: false }); }, [data.refreshScenarios, startAssessment]);
  useEffect(() => { if (!job || ["completed", "failed"].includes(job.status)) return; const timer = window.setInterval(() => apiRequest<JobState>(`/api/jobs/${job.job_id}`).then((next) => { setJob(next); if (next.status === "completed" && next.result) { setRun(next.result); setView("assessment"); void data.refreshRuns(); } }).catch((reason) => setJob({ ...job, status: "failed", progress: 100, error: reason instanceof Error ? reason.message : "Job polling failed." })), 900); return () => window.clearInterval(timer); }, [job, data.refreshRuns]);
  const logout = async () => { await apiRequest("/api/auth/logout", { method: "POST" }); setSession({ authenticated: false, email: null }); setRun(null); setView("overview"); }; const approve = async (name: string) => { if (!run) return; try { const approved = await apiRequest<RunDetail>(`/api/runs/${run.run_id}/approve-repair`, { method: "POST", body: JSON.stringify({ reviewer_name: name }) }); setRun(approved); setShowApproval(false); await data.refreshRuns(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Replay failed."); } };
  const content = useMemo(() => { if (data.initializing) return <main className="main-content"><div className="loading-panel">Opening workspace…</div></main>; if (view === "overview") return <OverviewView runs={data.runs} scenarios={data.scenarios} health={data.health} onNew={() => openNew("guided")} onCatalog={() => setView("assessments")} onConnections={() => setView("connections")} onSelectRun={selectRun} />; if (view === "assessments") return <AssessmentsView scenarios={data.scenarios} onRun={(id) => openNew("guided", id)} onImport={() => openNew("custom")} />; if (view === "runs") return <RunsView runs={data.runs} onSelect={selectRun} />; if (view === "connections") return <ConnectionsView data={data.connections} onRefresh={data.refreshConnections} onSelect={setSelectedConnection} />; if (run) return <AssessmentView run={run} onApprove={() => setShowApproval(true)} onEvidence={() => setShowEvidence(true)} onRetry={() => openNew("guided", run.scenario_id)} />; return <OverviewView runs={data.runs} scenarios={data.scenarios} health={data.health} onNew={() => openNew("guided")} onCatalog={() => setView("assessments")} onConnections={() => setView("connections")} onSelectRun={selectRun} />; }, [data, view, run, selectRun]);
  if (sessionLoading) return <div className="login-loading"><ShieldCheckIcon />CutoverProof</div>; if (!session?.authenticated) return <LoginView onSignedIn={setSession} />;
  return <AppShell view={view} email={session.email ?? "engineer@cutoverproof.dev"} onView={setView} onNew={() => openNew("guided")} onLogout={() => void logout()}>{error ? <div className="error-toast"><ExclamationTriangleIcon /><span>{error}</span><button onClick={() => setError(null)}><XMarkIcon /></button></div> : null}{job && job.status !== "completed" ? <JobBanner job={job} /> : null}{content}{showNew ? <NewAssessmentModal scenarios={data.scenarios} initialScenario={initialScenario} mode={newMode} health={data.health} onClose={() => setShowNew(false)} onStart={startAssessment} onImportAndStart={importAndStart} /> : null}{showApproval && run ? <ApprovalModal run={run} onClose={() => setShowApproval(false)} onApprove={approve} /> : null}{showEvidence && run ? <EvidenceModal run={run} onClose={() => setShowEvidence(false)} /> : null}</AppShell>;
}

function ProductOverview({
  onTour,
  onNewAssessment,
  onReviewDraft,
  onSelectRun,
  latestDraft,
  runs,
  webMcp,
}: {
  onTour: () => void;
  onNewAssessment: () => void;
  onReviewDraft: (scenarioId: string) => void;
  onSelectRun: (runId: string) => void;
  latestDraft: ChangeReviewDraft | null;
  runs: RunSummary[];
  webMcp: WebMcpAvailability;
}) {
  const toolStatus = webMcp.ready
    ? `${webMcp.toolCount} browser tools ready`
    : webMcp.supported
      ? "Connecting browser tools"
      : "Human controls active";
  return (
    <main className="main-content overview-view workspace-home">
      <section className="workspace-heading change-control-heading">
        <div>
          <p className="eyebrow">Production change control</p>
          <h1>Prove the change before you cut over.</h1>
          <p>Agents prepare the case. PostgreSQL produces the evidence. You keep authority.</p>
        </div>
        <span className={`webmcp-status ${webMcp.ready ? "ready" : ""}`}><span />{toolStatus}</span>
      </section>

      <section className="first-assessment" data-tour="how-it-works">
        <div className="first-assessment-copy">
          <p className="eyebrow">Shared change contract</p>
          <h2>One decision. Three independent authorities.</h2>
          <p>Every migration stays inside a declared contract: bounded operations, explicit invariants, and a named human decision.</p>
        </div>
        <ol className="workflow-steps authority-steps">
          <li><span><CodeBracketSquareIcon /></span><div><small>Agent</small><strong>Prepare</strong><p>Inspect the contract, focus the risks, and create a visible review draft.</p></div></li>
          <li><span><CircleStackIcon /></span><div><small>Verifier</small><strong>Prove</strong><p>Execute only declared operations and decide invariants with PostgreSQL evidence.</p></div></li>
          <li><span><UserCircleIcon /></span><div><small>Human</small><strong>Authorize</strong><p>Start the sandbox run and approve any bounded repair replay by name.</p></div></li>
        </ol>
        <footer>
          <button className="primary-button first-assessment-cta" onClick={onTour}><PlayIcon />Run guided demo</button>
          <button className="secondary-button first-assessment-cta" data-tour="new-assessment" onClick={onNewAssessment}><PlusIcon />New assessment</button>
        </footer>
      </section>

      {latestDraft ? <section className="agent-review-card" aria-live="polite">
        <div className="agent-review-icon"><CodeBracketSquareIcon /></div>
        <div className="agent-review-copy">
          <div className="agent-review-meta"><span>Agent-prepared review</span><span>Awaiting you</span></div>
          <h2>{latestDraft.contract_name}</h2>
          <p>{latestDraft.objective}</p>
          {latestDraft.risk_focus.length ? <ul>{latestDraft.risk_focus.map((risk) => <li key={risk}>{risk.replaceAll("_", " ")}</li>)}</ul> : null}
          <small><LockClosedIcon />Nothing has executed. A human must start the sandbox assessment.</small>
        </div>
        <button className="primary-button" onClick={() => onReviewDraft(latestDraft.scenario_id)}>Review &amp; run</button>
      </section> : null}

      <section className="control-boundary" aria-label="CutoverProof authority boundary">
        <div><ShieldCheckIcon /><span><strong>Agent-readable</strong><small>Contracts and verified evidence</small></span></div>
        <div><LockClosedIcon /><span><strong>Human-gated</strong><small>Run start and repair approval</small></span></div>
        <div><CircleStackIcon /><span><strong>Verifier-owned</strong><small>Pass, block, and replay verdicts</small></span></div>
      </section>

      <section className="recent-runs-section">
        <div className="section-heading compact-heading"><div><p className="eyebrow">Decision history</p><h2>Recent assessments</h2></div></div>
        {runs.length ? <div className="assessment-list compact-assessment-list">{runs.slice(0, 3).map((item) => <article key={item.run_id}>
          <div className="assessment-list-copy"><small>{item.status_label}</small><h2>{item.title}</h2><p>{item.scenario_name}</p></div>
          <dl><div><dt>Candidates</dt><dd>{item.candidates_attempted}/{item.max_budget}</dd></div><div><dt>Runtime</dt><dd>{item.wall_clock_seconds}s</dd></div></dl>
          <button className="secondary-button" onClick={() => onSelectRun(item.run_id)}>Open</button>
        </article>)}</div> : <p className="empty-history">No decisions yet. Run the guided demo or let your browser agent prepare a review.</p>}
      </section>
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
    title: "See how CutoverProof finds a migration bug",
    body: "This tour uses a sample migration and shows the exact database row that fails.",
  },
  {
    target: "[data-tour='how-it-works']",
    title: "One clear workflow",
    body: "Import a migration, test it in isolation, and review the result before you deploy.",
  },
  {
    target: "[data-tour='new-assessment']",
    title: "Bring your own migration",
    body: "For your own work, import the schema, seed data, allowed steps, and the SQL condition that must stay true.",
  },
  {
    target: "[data-tour='assessments-navigation']",
    title: "Review previous results",
    body: "Assessments keeps your completed checks and their technical evidence in one place.",
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
        <div className="import-actions">
          <button className="secondary-button" type="button" onClick={() => void loadTemplate()}>Load example template</button>
          <button className="secondary-button" type="button" onClick={() => fileRef.current?.click()}><ArrowUpTrayIcon />Choose JSON file</button>
          <input ref={fileRef} hidden type="file" accept="application/json" onChange={(event) => { const file = event.target.files?.[0]; if (file) void file.text().then((text) => { setJsonText(text); setSourceName(file.name); }); }} />
        </div>
        {jsonText ? <label className="configuration-editor"><span>Migration configuration <small>{sourceName}</small></span><textarea value={jsonText} onChange={(event) => setJsonText(event.target.value)} required /></label> : <p className="assessment-choice-copy">Load the example or choose a JSON file to continue.</p>}
        {!health?.model_configured ? <p className="form-warning">Gemini is not configured on this server.</p> : null}
        {error ? <p className="inline-error">{error}</p> : null}
        <footer><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={busy || !health?.model_configured || !jsonText.trim()}>{busy ? "Starting…" : "Run assessment"}</button></footer>
      </form>
    </Modal>
  );
}

export function AppV2() {
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

  useEffect(() => {
    if (active) void refreshReviewDrafts();
    else setReviewDrafts([]);
  }, [active, refreshReviewDrafts]);

  useEffect(() => {
    const handleReviewCreated = (event: Event) => {
      const draft = (event as CustomEvent<ChangeReviewDraft>).detail;
      if (!draft) return;
      setReviewDrafts((current) => [draft, ...current.filter((item) => item.id !== draft.id)]);
      setView("overview");
    };
    window.addEventListener(WEBMCP_REVIEW_CREATED, handleReviewCreated);
    return () => window.removeEventListener(WEBMCP_REVIEW_CREATED, handleReviewCreated);
  }, []);

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
    if (view === "overview") return <ProductOverview onTour={openTour} onNewAssessment={() => setShowCustom(true)} onReviewDraft={openGuided} onSelectRun={selectRun} latestDraft={latestDraft} runs={userRuns} webMcp={webMcp} />;
    if (view === "assessments") return <AssessmentHistoryView runs={userRuns} onNew={() => setShowCustom(true)} onSelect={selectRun} />;
    if (view === "settings") return <SettingsView email={session?.email ?? ""} health={data.health} connection={data.connections?.configured ?? null} preferences={preferences} onSave={savePreferences} onLogout={() => void logout()} />;
    if (view === "connections") return <ConnectionsView data={data.connections} onRefresh={data.refreshConnections} onSelect={setSelectedConnection} />;
    if (run) return <AssessmentView run={run} onApprove={() => setShowApproval(true)} onEvidence={() => setShowEvidence(true)} onRetry={() => openGuided(run.scenario_id)} />;
    return <ProductOverview onTour={openTour} onNewAssessment={() => setShowCustom(true)} onReviewDraft={openGuided} onSelectRun={selectRun} latestDraft={latestDraft} runs={userRuns} webMcp={webMcp} />;
  }, [data, view, run, selectRun, userRuns, session?.email, preferences, savePreferences, latestDraft, webMcp]);

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
