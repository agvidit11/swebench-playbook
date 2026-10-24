You are an expert panel in one: terminal & web UI/UX designer, product manager for developer tools, software
architect, and an engineering manager who runs many parallel AI agents across two servers. Review "workboard" in this
directory (README.md, DESIGN.md, skill/SKILL.md, workboard/*.py esp. projection.py insights.py html.py html_page.py
tui.py app_ui.py, tests/). Screenshots of the live web dashboard are attached (1 board, 2 hover card, 3 task card,
4 stats); terminal outputs are in /tmp/wb-review/5-terminal-board.txt and 6-terminal-stats.txt. Do not read
review/*.log.

Context: one author builds SWE-bench tasks on codimango with many Claude/Codex sessions across two devservers. The
board must show what to do next, who is on what (claims, presence, a free-text CLAIMS.md), and how the week is going.

The author's latest feedback (address every point; say what is still not met):
- hover text must be summarized: only important info; validation should show only warnings/failures, few words, with
  a suggested next step; green "all passed" noise is not wanted
- review column was not useful (bars inaccurate); now single/double ticks grey/green + human status — judge it
- task link "not so good"; card should start with next steps + ETA + which agent/server to assign
- sync meaning must be obvious; headers explain themselves on hover; copyable hover cards
- groups: needs you / ready / validating / with reviewers / done (accepted, in training, archived)
- small cute animations; "cuteness and UI are important", but readability first
- data freshness (author saw 3-4 min lag)
- sessions must have one place to read/update to avoid overlap (claims, presubmit results, new tasks)

Deliver review/codex-product-review.md with:
A. Verdict (5 lines): is this genuinely useful to the author today? biggest gaps.
B. DELETE: features/columns/commands/code that add noise or maintenance with little value (be bold; say why).
C. ADD: highest-value missing features, ranked, each with problem, concrete design, effort S/M/L.
D. MODIFY: concrete changes to existing UI/logic (column set, wording, colours, hover content, card layout, ETA
   logic, assignee logic, grouping, freshness), each with before -> after.
E. Making better use of the structure: how the board should coordinate agents and the two servers (assignment,
   load, handoffs, avoiding duplicate work), and what each session should do automatically vs explicitly.
F. ETA and next-step accuracy: what data exists (codimango, review history, git, ledger), how to compute honest
   ETAs with confidence, and what to show when unknown.
G. Visual critique of the screenshots: spacing, hierarchy, colour use, density, accessibility; 10 specific fixes.
H. Risks/bugs you can see in the code (data correctness, staleness, privacy, races) with file:line.
I. A prioritized 2-week roadmap (ordered list, each item <= 1 line).
Write only that file. Be specific and opinionated; no generic advice.

Budget note: read README.md, skill/SKILL.md, workboard/insights.py, workboard/projection.py, workboard/html_page.py (skim), and the terminal outputs; skim the rest only as needed. Write the review file early and refine it.
