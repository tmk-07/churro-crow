import { useEffect, useState } from "react";
import { getConfig } from "./api";
import { FALLBACK_CONFIG } from "./constants";
import type { ApiConfig } from "./types";
import { CheckerPage } from "./pages/CheckerPage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { LearnPage } from "./pages/LearnPage";
import { SolverPage } from "./pages/SolverPage";

type Page = "learn" | "check" | "solve" | "leaderboard";

function pageFromHash(): Page {
  const page = window.location.hash.replace("#/", "") as Page;
  return ["learn", "check", "solve", "leaderboard"].includes(page) ? page : "learn";
}

const navItems: Array<[Page, string]> = [
  ["learn", "Learn"],
  ["check", "Checker"],
  ["solve", "Solver"],
  ["leaderboard", "Leaderboard"],
];

export default function App() {
  const [page, setPage] = useState<Page>(pageFromHash());
  const [config, setConfig] = useState<ApiConfig>(FALLBACK_CONFIG);
  const [apiReady, setApiReady] = useState(true);

  useEffect(() => {
    const syncPage = () => setPage(pageFromHash());
    window.addEventListener("hashchange", syncPage);
    getConfig().then((next) => {
      setConfig(next);
      setApiReady(true);
    }).catch(() => setApiReady(false));
    return () => window.removeEventListener("hashchange", syncPage);
  }, []);

  const navigate = (next: string) => {
    window.location.hash = `#/${next}`;
    setPage(next as Page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="app-frame">
      <header className="site-header">
        <button className="brand" onClick={() => navigate("learn")}>
          <span className="brand-mark">OS</span>
          <span><strong>On-Sets Lab</strong><small>by Churro Crow</small></span>
        </button>
        <nav aria-label="Primary navigation">
          {navItems.map(([target, label]) => (
            <button className={page === target ? "active" : ""} onClick={() => navigate(target)} key={target}>{label}</button>
          ))}
        </nav>
        <span className={`api-status ${apiReady ? "online" : "offline"}`}>
          <i />{apiReady ? "Engine online" : "API pending"}
        </span>
      </header>

      {!apiReady && (
        <div className="migration-banner">
          The new interface is ready, but calculations stay on the Streamlit fallback until the API host is enabled.{" "}
          <a href="https://churro-crow-oscalc.streamlit.app/" target="_blank" rel="noreferrer">Open the working calculator</a>
        </div>
      )}

      {page === "learn" && <LearnPage onNavigate={navigate} />}
      {page === "check" && <CheckerPage config={config} />}
      {page === "solve" && <SolverPage config={config} />}
      {page === "leaderboard" && <LeaderboardPage />}

      <footer><span>AGLOA On-Sets ruleset 2026–27</span><span>onsets.tkimify.com</span></footer>
    </div>
  );
}
