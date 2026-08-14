# Churro Crow Revamp Plan

This is the living roadmap for rebuilding Churro Crow into an approachable On-Sets learning, practice, checking, and solving tool.

## Product direction

- Audience: anyone learning or practicing On-Sets.
- Runtime solving must be deterministic code, not AI-dependent.
- Keep Python and Streamlit for the initial revamp.
- Reconsider a Next.js frontend with a FastAPI backend only after a polished Streamlit release demonstrates a concrete UI limitation.
- Keep the leaderboard public and lightweight.

## Agreed rule contract

- Version tournament presets and saved problems by ruleset, beginning with `agloa-2026-27`.
- Evaluate explicit grouping first and primes before binary operations.
- Treat ungrouped binary operations as ambiguous: the checker evaluates every legal grouping, while the solver emits minimally ambiguous expressions.
- If a required cube inventory contains `c` or `=`, a restriction expression is mandatory.
- Whenever a restriction is written, every required cube appears in the restriction and every non-restriction required cube also appears in the solution expression.
- Restriction-only cubes (`c` and `=`) appear only in the restriction expression.
- The restriction and solution are separate expressions and may reuse the same physical cube inventory.
- Required and forbidden cards constrain the final answer.
- Selected/excluded cards and double-set cards alter the active universe.
- Model Now, Impossible, and Forceout solution-writing situations; do not simulate full matches.
- Allow any custom Universe size but warn when it is outside the selected division's tournament range.
- Use a single display notation while accepting normalized keyboard aliases.

## Phase 0 — Secure and normalize

Status: **Complete**

- [x] Back up both original Git repositories and all uncommitted work.
- [x] Flatten the accidentally nested canonical repository into the project root.
- [x] Preserve the current solver changes as unstaged work.
- [x] Revoke the exposed Google service-account key.
- [x] Remove credential-bearing files and generated artifacts from reachable Git history.
- [x] Force-update the sanitized `main` and debug branches on GitHub.
- [x] Move leaderboard credentials into encrypted Streamlit secrets.
- [x] Create and install a replacement Google service-account key.
- [x] Delete the downloaded replacement-key file after installation.
- [x] Add `.gitignore` and pin direct Python dependencies.
- [x] Verify the core evaluator, active Streamlit pages, and deployed leaderboard.

Recovery bundles are stored locally in `.phase0-backup-20260813/`. They contain the retired history and old revoked key, must never be uploaded, and can be deleted after the migration is no longer needed for recovery.

## Phase 1 — Specify and test the rules

Goal: make the intended game behavior executable and safe to change.

Status: **Complete**

- [x] Publish the versioned `agloa-2026-27` product rules contract in `docs/rules/2026-27.md`.
- [x] Turn the agreed rule contract above into automated tests.
- [x] Add initial golden problems with known restrictions, solutions, and resulting cards.
- [x] Test explicit grouping, prime precedence, and every legal binary-operation interpretation.
- [x] Test required/permitted inventory behavior with and without mandatory restrictions.
- [x] Test required and forbidden final cards.
- [x] Test card exclusions, double sets, `V`, and `Z`.
- [x] Test malformed expressions with useful error messages.
- [x] Add Streamlit page smoke tests to continuous integration.

Completion criteria:

- Every agreed rule has at least one positive and one edge-case test.
- Current intended behavior passes before the calculation engine is replaced.
- Test failures clearly identify the broken game rule.

## Phase 2 — Rebuild the calculation engine

Goal: replace mutable, brute-force calculation code with a reliable domain engine.

Status: **Complete locally; awaiting review**

- [x] Define immutable models for cards, universes, cube inventories, and results.
- [x] Build an expression tokenizer and parser that produces an expression tree.
- [x] Separate solution-expression and restriction-expression validation.
- [x] Remove mutable global universe and operation state from the active app.
- [x] Centralize cube-usage counting and inventory validation.
- [x] Return structured results instead of UI-formatted strings.
- [x] Make result ordering deterministic.
- [x] Reuse generated subexpressions and prune impossible inventory branches.
- [x] Deduplicate equivalent expressions and group identical result sets.
- [x] Add optional step-by-step evaluation explanations.
- [x] Keep compatibility imports for the legacy page entry points.

Completion criteria:

- All Phase 1 tests pass against the new engine.
- Identical inputs always return identically ordered answers.
- Normal solver inputs finish within an agreed interactive response time.
- The engine can run independently of Streamlit.

## Phase 3 — Add rule variations

Goal: implement variations as explicit, composable rules rather than global mutations.

Status: **Complete for the agreed computational scope; awaiting review**

Implemented scope:

1. [x] No Null Restrictions
2. [x] Symmetric Difference, including Double Set selection order
3. [x] Interchangeable `U` and `∩`
4. [x] Interchangeable `V` and `Z`
5. [x] Multiple Operations and Two Operations
6. [x] Wild Cube
7. [x] Blank Card Wild
8. [x] Double Set
9. [x] Required/Forbidden Card

Review refinements:

- [x] Track Wild Cube as one physical section/face/occurrence rather than making
  every matching face wild.
- [x] Search multiple independent Restrictions only after ordinary and chain
  Restriction strategies find no Solution.
- [x] Use plain no-result messaging for Impossible searches.

Deliberately outside this release:

- Official Two Solutions is not exposed. Normal solver output is grouped by
  physical card set and promotes different sets first.
- Absolute Value remains deferred while the product accepts one numeric Goal.
- Shift from Permitted and other move/scoring variations are outside the
  checker/solver product boundary.

For every variation:

- [x] Write its rule definition before implementation.
- [x] Add isolated tests.
- [x] Add combination tests with other supported variations.
- [x] Show the active variation and its effect in generated results.

No rule decisions remain for the implemented scope.

## Phase 4 — Rebuild the Streamlit experience

Goal: make the app understandable for beginners while remaining efficient for experienced players.

Status: **Complete locally; awaiting review**

Pages:

- [x] **Learn** — notation, cards, operations, examples, and situation guidance.
- [x] **Check** — evaluate a Restriction, Set-Name, or combined answer.
- [x] **Solve** — find answers from the complete physical game state and card constraints.
- [x] **Practice** — intentionally marked under construction until a later phase.
- [x] **Leaderboards** — existing public mode-specific rankings remain available.

Core UI work:

- [x] Replace manual session routing with Streamlit multipage navigation.
- [x] Build one reusable card-universe selector.
- [x] Lay out Required, Permitted, Forbidden, and Resource cube trays together.
- [x] Add clear required/forbidden card selection.
- [x] Validate inputs before starting expensive searches.
- [x] Show Restriction, Set-Name, physical cards, cube usage, and evaluation steps together.
- [x] Keep all controls visible for this review build; defer density/mode decisions.
- [x] Use responsive native Streamlit layout, keyboard-friendly controls, contrast, and explicit error states.
- [x] Confirm native controls are sufficient for this review build; no custom component added.

Completion criteria:

- A new learner can check and generate a basic answer without external instructions.
- All active pages work on desktop and mobile widths.
- UI code does not contain game-rule logic.

## Phase 5 — Practice and leaderboard hardening

Goal: make practice reliable and the public leaderboard safe enough for low-stakes use.

- [ ] Fix and test timer behavior across Streamlit reruns.
- [ ] Prevent duplicate score submissions.
- [ ] Validate and limit player names.
- [ ] Keep separate rankings for each practice mode.
- [ ] Consider recording attempted questions and accuracy.
- [ ] Add solution-finding practice after the solver is stable.
- [ ] Add graceful Google Sheets outage behavior.
- [ ] Verify score writes without exposing credentials or detailed service errors.
- [ ] Reassess Google Sheets only if usage or moderation needs outgrow it.

Completion criteria:

- A completed quiz can submit at most one score unless explicitly replayed.
- Timer and scoring behavior have automated tests.
- Leaderboard failure never prevents the rest of the app from working.

## Phase 6 — Deployment decision

Goal: choose the long-term interface and hosting stack using evidence from the rebuilt product.

- [ ] Deploy and evaluate the polished Streamlit release.
- [ ] Test mobile usability, interaction quality, performance, and maintainability.
- [ ] Document any concrete limitations that cannot be solved cleanly with Streamlit.
- [ ] Stay with Streamlit if it meets the product needs.
- [ ] If necessary, retain the Python engine behind FastAPI and rebuild only the frontend in Next.js.
- [ ] Add production monitoring, deployment checks, and rollback instructions for the chosen stack.

Do not split into separate frontend and backend deployments until Streamlit has demonstrated a specific blocking limitation.

## First revamped release

The first major release should contain:

- [x] Secure, normalized repository and deployed leaderboard credentials.
- [x] Tested rule contract.
- [x] Rebuilt expression parser and evaluator.
- [x] Correct Required/Permitted/Resource cube solver behavior by situation.
- [x] Understandable structured solver results grouped by physical card set.
- [x] No Null and the agreed computational variations.
- [x] Rebuilt Checker and Solver pages.
- [x] Public leaderboard carried forward; Practice intentionally deferred.

## Current next step

Review the local Phase 1–4 build. Do not deploy or begin Phase 5 until the review decisions are incorporated.
