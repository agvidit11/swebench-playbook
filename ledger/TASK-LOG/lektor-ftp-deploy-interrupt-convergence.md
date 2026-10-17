# lektor-ftp-deploy-interrupt-convergence
**Owner:** devvm6971 / lane-i
**State:** building 2026-10-17 (new single-turn task derived from the lektor-output-liveness-prune pivot; Vidit allowed creating it as new)

## History
- 2026-10-17 · lane-i · design+probe in ~/scratch/lane-i/lk-pivot (PIVOT-REPORT.md §5-§9): recovery capability 4/4 (too easy); publisher capability: blind statement + real pyftpdlib probe -> 0/4 genuine passes, hardened reference ref-ftp-v2 passes all, trivial delete-all-not-live passes. Upstream check: FtpConnection.delete_file bytes bug present on master; #555 fixed login/upload only; no issue/PR on interrupted-deploy convergence.
