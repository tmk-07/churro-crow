interface CardGridProps {
  cards: string[];
  selected: string[];
  onChange: (cards: string[]) => void;
}

export function CardGrid({ cards, selected, onChange }: CardGridProps) {
  const selectedSet = new Set(selected);
  const toggle = (card: string) => {
    const next = selectedSet.has(card)
      ? selected.filter((item) => item !== card)
      : cards.filter((item) => item === card || selectedSet.has(item));
    onChange(next);
  };

  return (
    <section className="field-section">
      <div className="section-heading">
        <div>
          <h2>Universe cards</h2>
          <p>Click a physical card to include or exclude it.</p>
        </div>
        <div className="inline-actions">
          <button type="button" className="text-button" onClick={() => onChange(cards)}>All</button>
          <button type="button" className="text-button" onClick={() => onChange([])}>Clear</button>
        </div>
      </div>
      <div className="card-grid">
        {cards.map((card) => {
          const active = selectedSet.has(card);
          return (
            <button
              type="button"
              key={card}
              className={`universe-card${active ? " selected" : ""}`}
              aria-pressed={active}
              onClick={() => toggle(card)}
            >
              <img src={`/cards/${card}.png`} alt={`${card} On-Sets card`} />
              <span>{active ? "✓ " : ""}{card}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
