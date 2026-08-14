export function LearnPage({ onNavigate }: { onNavigate: (page: string) => void }) {
  return (
    <main className="page-shell landing-page">
      <section className="hero">
        <div>
          <p className="eyebrow">AGLOA On-Sets · 2026–27</p>
          <h1>See the sets.<br />Test the logic.</h1>
          <p className="hero-copy">A focused checker and solution finder for learning, practice, and real game situations.</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => onNavigate("check")}>Check an expression</button>
            <button className="secondary-button" onClick={() => onNavigate("solve")}>Find solutions</button>
          </div>
        </div>
        <div className="hero-orbit" aria-hidden="true">
          <span className="orbit-card blue">B</span>
          <span className="orbit-card red">R</span>
          <span className="orbit-card green">G</span>
          <span className="orbit-card yellow">Y</span>
          <div className="orbit-center">∪</div>
        </div>
      </section>

      <section className="feature-grid">
        <article><span>01</span><h2>Build the Universe</h2><p>Use the familiar 4×4 chart to choose the physical cards in the shake.</p></article>
        <article><span>02</span><h2>Write the math</h2><p>Enter Set-Names and Restrictions with official On-Sets operations and variations.</p></article>
        <article><span>03</span><h2>Inspect the result</h2><p>See every legal grouping, physical card set, weighted value, and evaluation step.</p></article>
      </section>

      <section className="notation-panel">
        <div><p className="eyebrow">Core notation</p><h2>Everything you need, nothing you don’t.</h2></div>
        <div className="notation-grid">
          {[
            ["V", "Universe"], ["Z", "Null set"], ["∪", "Union"], ["∩", "Intersection"],
            ["−", "Subtraction"], ["′", "Complement"], ["⊂", "Subset restriction"], ["=", "Equals restriction"],
          ].map(([symbol, label]) => <div key={label}><strong>{symbol}</strong><span>{label}</span></div>)}
        </div>
      </section>
    </main>
  );
}
