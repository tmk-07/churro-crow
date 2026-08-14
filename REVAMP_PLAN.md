# Churro Crow Revamp Plan

This is the living roadmap for rebuilding Churro Crow into an approachable On-Sets learning, practice, checking, and solving tool.

## Product direction

- Audience: anyone learning or practicing On-Sets.
- Runtime solving must be deterministic code, not AI-dependent.
- Keep Python and Streamlit for the initial revamp.
- Reconsider a Next.js frontend with a FastAPI backend only after a polished Streamlit release demonstrates a concrete UI limitation.
- Keep the leaderboard public and lightweight.

## Agreed rule contract

- Evaluate expressions inside parentheses first.
- Apply primes before binary operations.
- Evaluate all other operations left to right with equal precedence.
- If a required cube inventory contains `c` or `=`, a restriction expression is mandatory.
- When a restriction is mandatory, every applicable required cube must appear independently in both the restriction and solution expressions.
- Restriction-only cubes (`c` and `=`) appear only in the restriction expression.
- The restriction and solution are separate expressions and may reuse the same physical cube inventory.
- If no restriction cube is required, required cubes apply only to the solution expression.
- Required and forbidden cards constrain the final answer.
- Selected/excluded cards and double-set cards alter the active universe.

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

- [ ] Turn the agreed rule contract above into automated tests.
- [ ] Add golden problems with known restrictions, solutions, and resulting cards.
- [ ] Test parentheses, prime precedence, and left-to-right evaluation.
- [ ] Test required/permitted inventory behavior with and without mandatory restrictions.
- [ ] Test required and forbidden final cards.
- [ ] Test card exclusions, double sets, `V`, and `Z`.
- [ ] Test malformed expressions with useful error messages.
- [ ] Add Streamlit page smoke tests to continuous integration.

Completion criteria:

- Every agreed rule has at least one positive and one edge-case test.
- Current intended behavior passes before the calculation engine is replaced.
- Test failures clearly identify the broken game rule.

## Phase 2 — Rebuild the calculation engine

Goal: replace mutable, brute-force calculation code with a reliable domain engine.

- [ ] Define immutable models for cards, universes, cube inventories, and results.
- [ ] Build an expression tokenizer and parser that produces an expression tree.
- [ ] Separate solution-expression and restriction-expression validation.
- [ ] Remove mutable global universe and operation state.
- [ ] Centralize cube-usage counting and inventory validation.
- [ ] Return structured results instead of UI-formatted strings.
- [ ] Make result ordering deterministic.
- [ ] Cache reusable subexpressions and prune impossible search branches.
- [ ] Deduplicate equivalent expressions and identical result sets.
- [ ] Add optional step-by-step evaluation explanations.
- [ ] Keep compatibility adapters until the Streamlit pages use the new API.

Completion criteria:

- All Phase 1 tests pass against the new engine.
- Identical inputs always return identically ordered answers.
- Normal solver inputs finish within an agreed interactive response time.
- The engine can run independently of Streamlit.

## Phase 3 — Add rule variations

Goal: implement variations as explicit, composable rules rather than global mutations.

Priority order:

1. [ ] No Null
2. [ ] Two Solutions
3. [ ] Symmetric difference cleanup
4. [ ] Interchangeable `u` and `n`
5. [ ] Interchangeable `V` and `Z`
6. [ ] MOPS and TOPS
7. [ ] Black/wild cubes
8. [ ] Additional tournament variations

For every variation:

- [ ] Write its rule definition before implementation.
- [ ] Add isolated tests.
- [ ] Add combination tests with other supported variations.
- [ ] Show the active variation and its effect in generated results.

Decisions still required:

- Define whether **No Null** removes the blank card, bans the `Z` cube, rejects empty intermediate/final sets, or combines those behaviors.
- Define whether **Two Solutions** means two expressions for one final set or two distinct final card sets from the same resources.

## Phase 4 — Rebuild the Streamlit experience

Goal: make the app understandable for beginners while remaining efficient for experienced players.

Planned pages:

- [ ] **Learn** — notation, cards, operations, examples, and walkthroughs.
- [ ] **Check** — evaluate a restriction, solution, or combined answer.
- [ ] **Solve** — find answers from physical cube resources and card constraints.
- [ ] **Practice** — padding, restrictions, solution finding, and future drills.
- [ ] **Leaderboards** — public mode-specific rankings.

Core UI work:

- [ ] Replace manual session routing with Streamlit multipage navigation.
- [ ] Build one reusable card-universe selector.
- [ ] Add visual Required and Permitted cube trays.
- [ ] Add clear required/forbidden card selection.
- [ ] Validate inputs before starting expensive searches.
- [ ] Show restriction, solution, cards, cube usage, and evaluation steps together.
- [ ] Provide beginner explanations and an advanced compact mode.
- [ ] Improve mobile layout, keyboard access, contrast, and error states.
- [ ] Add a custom Streamlit component only if native controls cannot support the cube/card interactions cleanly.

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
- [ ] Tested rule contract.
- [ ] Rebuilt expression parser and evaluator.
- [ ] Correct required/permitted cube solver behavior.
- [ ] Understandable structured solver results.
- [ ] No Null support.
- [ ] Two Solutions support.
- [ ] Rebuilt Checker and Solver pages.
- [ ] Existing practice modes and public leaderboard carried forward safely.

## Current next step

Start **Phase 1** by documenting the remaining No Null and Two Solutions definitions, then build the rule-focused test suite around the current engine.
