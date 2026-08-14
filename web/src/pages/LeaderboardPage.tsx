const boards = [
  {
    title: "Padding Practice",
    scores: [
      ["riya", 71, "2025-10-12"],
      ["Will", 62, "2025-10-06"],
      ["jennifer", 61, "2025-10-02"],
      ["jennifer x.", 55, "2025-09-25"],
      ["jennifer x", 54, "2025-09-26"],
    ],
  },
  {
    title: "Restrictions",
    scores: [
      ["riya", 66, "2025-10-12"],
      ["Will", 57, "2025-10-01"],
      ["jennifer", 47, "2025-10-01"],
      ["tk", 32, "2025-08-21"],
      ["Caleb W", 17, "2025-09-16"],
    ],
  },
  {
    title: "SymDiff Padding",
    scores: [
      ["riya", 64, "2025-10-06"],
      ["Will", 38, "2025-09-22"],
      ["Caleb W", 27, "2025-09-17"],
      ["tk", 25, "2025-08-21"],
      ["symdiff", 15, ""],
    ],
  },
] as const;

export function LeaderboardPage() {
  return (
    <main className="page-shell">
      <header className="page-header">
        <p className="eyebrow">Frozen snapshot</p>
        <h1>Practice leaderboards.</h1>
        <p>These standings are read-only while practice mode is rebuilt for the new application.</p>
      </header>
      <div className="leaderboard-grid">
        {boards.map((board) => (
          <section className="leaderboard-card" key={board.title}>
            <h2>{board.title}</h2>
            <ol>
              {board.scores.map(([player, score, date], index) => (
                <li key={`${player}-${index}`}>
                  <span className="rank">{index + 1}</span>
                  <span className="player"><strong>{player}</strong><small>{date || "No date recorded"}</small></span>
                  <strong className="score">{score}</strong>
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>
      <div className="notice info">New score submissions remain paused until practice mode has migrated.</div>
    </main>
  );
}
