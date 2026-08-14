import { FormEvent, useState } from "react";
import { ApiError, solveShake } from "../api";
import { CARD_ORDER, DEFAULT_VARIATIONS, SITUATION_HELP, SITUATION_LABELS } from "../constants";
import type { ApiConfig, Division, Situation, SolveResponse, VariationPayload } from "../types";
import { inventoryText } from "../utils";
import { CardGrid } from "../components/CardGrid";
import { DivisionSelect } from "../components/DivisionSelect";
import { ErrorNotice, Notice } from "../components/Notice";
import { CardList, Steps } from "../components/ResultParts";
import { VariationPanel } from "../components/VariationPanel";

type CubeSections = { required: string; permitted: string; forbidden: string; resources: string };
const emptyCubes: CubeSections = { required: "", permitted: "", forbidden: "", resources: "" };

export function SolverPage({ config }: { config: ApiConfig }) {
  const [division, setDivision] = useState<Division>("senior");
  const [situation, setSituation] = useState<Situation>("impossible");
  const [goal, setGoal] = useState(6);
  const [universe, setUniverse] = useState<string[]>(CARD_ORDER);
  const [cubes, setCubes] = useState<CubeSections>(emptyCubes);
  const [variations, setVariations] = useState<VariationPayload>(DEFAULT_VARIATIONS);
  const [requested, setRequested] = useState(5);
  const [timeLimit, setTimeLimit] = useState(5);
  const [proceedAnyway, setProceedAnyway] = useState(false);
  const [report, setReport] = useState<SolveResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [running, setRunning] = useState(false);

  const run = async (nextRequested = requested) => {
    setRunning(true);
    setError(null);
    try {
      const result = await solveShake({
        universe,
        division,
        situation,
        goal,
        ...cubes,
        variations,
        requested: nextRequested,
        time_limit_seconds: timeLimit,
        proceed_anyway: proceedAnyway,
      });
      setReport(result);
    } catch (caught) {
      setReport(null);
      setError(caught);
      if (caught instanceof ApiError && caught.issues.length) setProceedAnyway(false);
    } finally {
      setRunning(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void run();
  };

  const more = () => {
    const next = Math.min(100, requested + 5);
    setRequested(next);
    void run(next);
  };

  return (
    <main className="page-shell">
      <header className="page-header">
        <p className="eyebrow">Solution finder</p>
        <h1>Model the shake. Search the legal space.</h1>
        <p>Results are grouped by distinct physical card set, with alternate written forms nested inside.</p>
      </header>

      <form onSubmit={submit} className="workspace-stack">
        <section className="panel compact-panel">
          <div className="form-grid three-up">
            <DivisionSelect value={division} onChange={setDivision} />
            <label>
              <span>Numeric Goal</span>
              <input type="number" min="0" value={goal} onChange={(event) => setGoal(Number(event.target.value))} />
            </label>
            <label>
              <span>Ruleset</span>
              <input value={config.ruleset_id} disabled />
            </label>
          </div>
          <fieldset className="situation-fieldset">
            <legend>Solution-writing context</legend>
            <div className="situation-grid">
              {(Object.keys(SITUATION_LABELS) as Situation[]).map((item) => (
                <label className={situation === item ? "selected" : ""} key={item}>
                  <input type="radio" name="situation" checked={situation === item} onChange={() => setSituation(item)} />
                  <strong>{SITUATION_LABELS[item]}</strong>
                  <span>{SITUATION_HELP[item]}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </section>

        <CardGrid cards={config.card_order} selected={universe} onChange={setUniverse} />

        <section className="panel">
          <div className="section-heading"><div><h2>Cube trays</h2><p>Use faces such as <code>rrggbbyy--nu</code>. Spaces are optional.</p></div></div>
          <div className="form-grid four-up cube-trays">
            {(Object.keys(cubes) as Array<keyof CubeSections>).map((section) => (
              <label key={section}>
                <span>{section[0].toUpperCase() + section.slice(1)}</span>
                <input
                  value={cubes[section]}
                  onChange={(event) => setCubes({ ...cubes, [section]: event.target.value })}
                  placeholder={section === "required" ? "--nuc" : section === "permitted" ? "rrrrbgy" : ""}
                />
              </label>
            ))}
          </div>
        </section>

        <VariationPanel
          config={config}
          division={division}
          universe={universe}
          value={variations}
          onChange={setVariations}
          cubeSections={cubes}
        />

        <section className="panel run-panel">
          <div className="form-grid three-up">
            <label>
              <span>Unique card-set solutions wanted</span>
              <input type="number" min="1" max="100" value={requested} onChange={(event) => setRequested(Number(event.target.value))} />
              <small>Alternate expressions do not consume this count.</small>
            </label>
            <label>
              <span>Interactive search limit</span>
              <div className="input-suffix"><input type="number" min="1" max="60" value={timeLimit} onChange={(event) => setTimeLimit(Number(event.target.value))} /><span>seconds</span></div>
            </label>
            <div className="button-align"><button className="primary-button" type="submit" disabled={running}>{running ? "Searching…" : "Generate solutions"}</button></div>
          </div>
          {error instanceof ApiError && error.issues.length > 0 && (
            <label className="inline-check proceed-check">
              <input checked={proceedAnyway} onChange={(event) => setProceedAnyway(event.target.checked)} type="checkbox" />
              Proceed anyway after reviewing these variation warnings
            </label>
          )}
        </section>
      </form>

      {error != null && <ErrorNotice error={error} />}
      {report?.warnings.map((warning) => <Notice tone="info" key={warning}>{warning}</Notice>)}

      {report && (
        <section className="results-section">
          <div className="metric-grid">
            <div><span>Unique solutions</span><strong>{report.returned}</strong></div>
            <div><span>Written variations</span><strong>{report.groups.reduce((sum, group) => sum + group.answers.length, 0)}</strong></div>
            <div><span>Search time</span><strong>{report.elapsed_seconds.toFixed(2)}s</strong></div>
          </div>

          {report.groups.length === 0 && <Notice tone="warning">Nothing was found.</Notice>}

          <div className="solution-groups">
            {report.groups.map((group, groupIndex) => (
              <details className="solution-group" open={groupIndex === 0} key={`${group.cards.join("-")}-${groupIndex}`}>
                <summary>
                  <span className="group-number">{groupIndex + 1}</span>
                  <span><strong>Card set {groupIndex + 1}</strong><CardList cards={group.cards} doubled={group.doubled_cards} /></span>
                  <span className="goal-chip">Goal {group.value}</span>
                </summary>
                <div className="solution-group-body">
                  {group.doubled_cards.length > 0 && <p className="muted">Cards marked (2) count twice under Double Set.</p>}
                  {group.answers.map((answer, answerIndex) => (
                    <article className="answer-card" key={`${answer.solution}-${answer.restriction}-${answerIndex}`}>
                      <div className="answer-heading"><span>Written variation {answerIndex + 1}</span><span>{answer.cube_count} written cubes</span></div>
                      {answer.restriction && <div className="expression-block"><span>Restriction</span><code>{answer.restriction}</code></div>}
                      <div className="expression-block"><span>Set-Name</span><code>{answer.solution}</code></div>
                      <div className="use-grid">
                        <div><span>Written cubes</span><strong>{inventoryText(answer.cube_use.written)}</strong></div>
                        <div><span>Physical cubes</span><strong>{inventoryText(answer.cube_use.physical)}</strong></div>
                        <div><span>Resources used</span><strong>{inventoryText(answer.resource_inventory)}</strong></div>
                      </div>
                      {answer.variation_notes.length > 0 && <p className="muted">{answer.variation_notes.join(" · ")}</p>}
                      <Steps steps={answer.steps} />
                    </article>
                  ))}
                </div>
              </details>
            ))}
          </div>

          {report.groups.length > 0 && <button className="secondary-button" type="button" onClick={more} disabled={running}>Find 5 more unique solutions</button>}
        </section>
      )}
    </main>
  );
}
