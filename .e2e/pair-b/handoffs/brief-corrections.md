# Brief vs runbook vs coordinator — recorded discrepancies (Pair B)

1. **"Exactly two steps" — WITHDRAWN by coordinator, 2026-10-02.** kustomize-localize-source-fidelity
   (3-step) was ACCEPTED; go-zero-flush (review) and protoc-epoch (passing) are 3-step. Rule now:
   3 declared steps unlock the single-1.0 exemption — ONE non-final step may read 1.0 if every other
   step is 1-3/5; the LAST step is never exempt. Use 2 or 3 steps as the cascade honestly supports.
   R11's "0 of 48 accepted tasks have 3+" is now false and should be corrected in R11 and A3 GATE 7.
   Pair-B implication: a saturated BUILD step can be the exempt step, but a task still needs two
   in-band steps, one of them last. The exemption does not remove the discriminator problem.

2. **B6 writes verdicts to `<task>/audit/review-gate/`** while the brief forbids any Claude write
   under a task dir including audit/. Resolution used: run review-gate.sh against a /tmp copy of
   the task tree; nothing Claude-authored lands in the task dir.

3. **avocado-brief.sh defaults its output to `<task>/audit/...`** — must always be given an
   explicit /tmp output path.

4. **mc.sh is dead (MetaCode retired 2026-09-29); A2/A3 still name it.** mc2.sh (`muse exec`) used.

5. **mc2.sh wrapper can return before the muse worker exits.** Two probes graded mid-edit and had
   to discard. Every probe brief now says: wait for the muse process to exit before grading.

6. **team-aai guard false positives** on Bash reads of scratch files when a loop variable builds the
   path, and on any heredoc containing the string "instruction.md". Worked around with literal
   paths / Write tool to /tmp; no guard was bypassed for a task-dir write.
