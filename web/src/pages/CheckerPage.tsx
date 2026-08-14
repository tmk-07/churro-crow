import { FormEvent, useMemo, useState } from "react";
import { ApiError, checkExpression } from "../api";
import { CARD_ORDER, DEFAULT_VARIATIONS } from "../constants";
import type { ApiConfig, CheckAnswer, CheckResponse, Division, VariationPayload } from "../types";
import { answersByValue, cardsText } from "../utils";
import { CardGrid } from "../components/CardGrid";
import { DivisionSelect } from "../components/DivisionSelect";
import { ErrorNotice, Notice } from "../components/Notice";
import { CardList, Steps } from "../components/ResultParts";
import { VariationPanel } from "../components/VariationPanel";

export function CheckerPage({ config }: { config: ApiConfig }) {
  const [division, setDivision] = useState<Division>("senior");
  const [universe, setUniverse] = useState<string[]>(CARD_ORDER);
  const [restriction, setRestriction] = useState("");
  const [solution, setSolution] = useState("");
  const [variations, setVariations] = useState<VariationPayload>(DEFAULT_VARIATIONS);
  const [proceedAnyway, setProceedAnyway] = useState(false);
  const [report, setReport] = useState<CheckResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [running, setRunning] = useState(false);
  const [selectedValue, setSelectedValue] = useState<number | null>(null);

  const grouped = useMemo(() => report ? answersByValue(report.answers) : new Map(), [report]);
  const shownValue = selectedValue != null && grouped.has(selectedValue)
    ? selectedValue
    : grouped.keys().next().value as number | undefined;
  const visibleAnswers: CheckAnswer[] = shownValue == null
    ? []
    : grouped.get(shownValue) ?? [];

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setRunning(true);
    setError(null);
    try {
      const result = await checkExpression({
        universe,
        division,
        restriction,
        solution,
        variations,
        proceed_anyway: proceedAnyway,
      });
      setReport(result);
      setSelectedValue(result.answers[0]?.value ?? null);
    } catch (caught) {
      setReport(null);
      setError(caught);
      if (caught instanceof ApiError && caught.issues.length) setProceedAnyway(false);
    } finally {
      setRunning(false);
    }
  };

  return (
    <main className="page-shell">
      <header className="page-header">
        <p className="eyebrow">Expression lab</p>
        <h1>Check every legal interpretation.</h1>
        <p>Enter a Set-Name, a Restriction, or both. Results are sorted by value and fully parenthesized.</p>
      </header>

      <form onSubmit={submit} className="workspace-stack">
        <section className="panel compact-panel">
          <div className="form-grid three-up">
            <DivisionSelect value={division} onChange={setDivision} />
            <label className="span-two">
              <span>Ruleset</span>
              <input value={config.ruleset_id} disabled />
            </label>
          </div>
        </section>

        <CardGrid cards={config.card_order} selected={universe} onChange={setUniverse} />

        <VariationPanel
          checker
          config={config}
          division={division}
          universe={universe}
          value={variations}
          onChange={setVariations}
        />

        <section className="panel">
          <div className="form-grid two-up expression-inputs">
            <label>
              <span>Restriction(s), optional</span>
              <textarea
                value={restriction}
                onChange={(event) => setRestriction(event.target.value)}
                placeholder="B ⊂ R, or one statement per line"
                rows={3}
              />
            </label>
            <label>
              <span>Set-Name, optional</span>
              <input
                value={solution}
                onChange={(event) => setSolution(event.target.value)}
                placeholder="B U G − R"
              />
            </label>
          </div>
          {error instanceof ApiError && error.issues.length > 0 && (
            <label className="inline-check proceed-check">
              <input checked={proceedAnyway} onChange={(event) => setProceedAnyway(event.target.checked)} type="checkbox" />
              Proceed anyway after reviewing these variation warnings
            </label>
          )}
          <button className="primary-button" type="submit" disabled={running}>
            {running ? "Checking…" : "Check expression"}
          </button>
        </section>
      </form>

      {error != null && <ErrorNotice error={error} />}
      {report?.warnings.map((warning) => <Notice tone="warning" key={warning}>{warning}</Notice>)}

      {report && report.restriction_interpretations.length > 0 && (
        <section className="results-section">
          <div className="results-heading">
            <div><p className="eyebrow">Restriction results</p><h2>{report.restriction_interpretations.length} legal interpretation(s)</h2></div>
          </div>
          {report.restriction_interpretations.map((interpretation, index) => (
            <article className="result-card" key={index}>
              <h3>Interpretation {index + 1}</h3>
              {interpretation.restrictions.map((item) => (
                <div className="result-row" key={item.expression}>
                  <code>{item.expression}</code>
                  <span>Removed: {cardsText(item.removed_cards)}</span>
                </div>
              ))}
              <p><strong>Remaining Universe:</strong> {cardsText(interpretation.remaining_universe)}</p>
            </article>
          ))}
        </section>
      )}

      {report && report.answers.length > 0 && (
        <section className="results-section">
          <div className="results-heading">
            <div>
              <p className="eyebrow">Checker results</p>
              <h2>{report.answers.length} legal interpretation{report.answers.length === 1 ? "" : "s"}</h2>
            </div>
            <div className="value-tabs" aria-label="Filter interpretations by value">
              {[...grouped.entries()].map(([value, answers]) => (
                <button
                  type="button"
                  className={shownValue === value ? "active" : ""}
                  key={value}
                  onClick={() => setSelectedValue(value)}
                >
                  Value {value}<small>{answers.length}</small>
                </button>
              ))}
            </div>
          </div>

          {visibleAnswers.map((answer, index) => (
            <article className="result-card" key={`${answer.expression}-${index}`}>
              <div className="result-title-row">
                <div><p className="eyebrow">Interpretation {index + 1}</p><code className="expression-code">{answer.expression}</code></div>
                <div className="value-badge"><span>Value</span><strong>{answer.value}</strong></div>
              </div>
              {answer.restriction && (
                <div className="restriction-block">
                  <span>Restriction</span><code>{answer.restriction}</code>
                  <small>Restricted Universe: {cardsText(answer.restricted_universe)}</small>
                </div>
              )}
              <div className="physical-cards"><span>Physical cards</span><CardList cards={answer.cards} doubled={answer.doubled_cards} /></div>
              {answer.doubled_cards.length > 0 && <small>Cards marked (2) count twice.</small>}
              {answer.violations.map((violation) => <Notice tone="warning" key={violation}>{violation}</Notice>)}
              <Steps steps={answer.steps} />
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
