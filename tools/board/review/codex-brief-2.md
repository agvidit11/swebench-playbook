Round 2. You reviewed DESIGN.md v1 in review/codex-review-1.md. DESIGN.md is now v2. Read both.
Author decisions that are FIXED (do not argue them, only make them safe): accepted includes used_in_training;
R2 = two distinct agent sessions on the same commit; contribution stats per session/host/model stay (private,
labelled non-causal, min sample); hooks may block edits when a healthy claim names another live session.
Tasks:
1. For each of your 10 top changes, say ADDRESSED / PARTLY / NOT, with one line why.
2. Scrutinise the new atomic claim design (create-only `refs/claims/<task>` pushed to GitHub over ssh, release
   via --force-with-lease, steal after expiry). Is a create-only ref push really atomic on GitHub? Failure modes
   (ref namespace permissions, push rules, force-push, lease semantics, GC, many refs, offline) and fixes.
3. Anything still unsafe, missing, or over-scoped for v1 (section 12). Keep it to what blocks building.
4. Final verdict: SIGN-OFF or REVISE (with the exact remaining edits).
Write to review/codex-review-2.md only. Concise.
