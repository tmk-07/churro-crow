import type { EvaluationStep } from "../types";
import { cardsText } from "../utils";

export function CardList({ cards, doubled = [] }: { cards: string[]; doubled?: string[] }) {
  return <span className="card-list">{cardsText(cards, doubled)}</span>;
}

export function Steps({ steps }: { steps: EvaluationStep[] }) {
  return (
    <details className="steps">
      <summary>Evaluation steps</summary>
      <ol>
        {steps.map((step, index) => (
          <li key={`${step.expression}-${index}`}>
            <code>{step.expression}</code>
            <span>{step.explanation}</span>
            <CardList cards={step.cards} />
          </li>
        ))}
      </ol>
    </details>
  );
}
