#!/usr/bin/env python3
"""Regenerate every presubmit run and summary, failing closed on infrastructure errors."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
RUNS = HERE / "presubmit-runs"
FAIL_RE = re.compile(r"^\s*FAIL\s+([^:]+):", re.MULTILINE)
STATUS_RE = re.compile(r"^\s*Review status:\s*(\S+)", re.MULTILINE)


def run_task(task, repo, ref):
    command = [sys.executable, str(PACKAGE / "presubmit.py"), task,
               "--repo", repo, "--ref", ref, "--color", "never"]
    run = subprocess.run(command, cwd=PACKAGE, capture_output=True, text=True)
    output = run.stdout
    if run.stderr:
        output += ("\n" if output and not output.endswith("\n") else "") + run.stderr
    output = f"# exit_code: {run.returncode}\n" + output
    status = STATUS_RE.search(output)
    return task, run.returncode, status.group(1) if status else None, FAIL_RE.findall(output), output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("tasks", nargs="*", help="optional task subset; default: every existing run file")
    args = parser.parse_args()
    tasks = args.tasks or sorted(path.stem for path in RUNS.glob("*.txt"))
    if not tasks:
        parser.error("no tasks found")

    ref_run = subprocess.run(["git", "-C", args.repo, "rev-parse", "origin/main"],
                             capture_output=True, text=True)
    ref = ref_run.stdout.strip()
    if ref_run.returncode or not re.fullmatch(r"[0-9a-f]{40}", ref):
        print("cannot resolve origin/main; fetch the task repository first", file=sys.stderr)
        return 2
    remote_run = subprocess.run(["git", "-C", args.repo, "remote", "get-url", "origin"],
                                capture_output=True, text=True)
    remote = remote_run.stdout.strip()
    advertised_run = subprocess.run(["git", "ls-remote", remote, "refs/heads/main"],
                                    capture_output=True, text=True) if remote else None
    advertised = advertised_run.stdout.split()[0] if advertised_run and advertised_run.stdout.split() else ""
    if (remote_run.returncode or not advertised_run or advertised_run.returncode
            or not re.fullmatch(r"[0-9a-f]{40}", advertised)):
        print("cannot verify origin/main without mutating refs", file=sys.stderr)
        return 2
    if advertised != ref:
        print(f"origin/main is stale ({ref[:8]} vs remote {advertised[:8]}); run git fetch",
              file=sys.stderr)
        return 2
    print(f"Pinned task repository ref: {ref}", flush=True)

    records = []
    infra = []
    outputs = {}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(run_task, task, args.repo, ref): task for task in tasks}
        for index, future in enumerate(as_completed(futures), 1):
            task = futures[future]
            try:
                task, returncode, status, failures, output = future.result()
            except Exception as error:  # noqa: BLE001
                infra.append((task, str(error)))
                print(f"[{index}/{len(tasks)}] {task}: infrastructure error", flush=True)
                continue
            outputs[task] = output
            print(f"[{index}/{len(tasks)}] {task}: exit {returncode}", flush=True)
            if returncode not in (0, 1):
                infra.append((task, returncode))
            elif not status:
                infra.append((task, "missing review status"))
            else:
                records.append((task, status, failures))

    if infra:
        print(f"refusing to rewrite summary: {len(infra)} infrastructure failure(s): {infra}",
              file=sys.stderr)
        return 2

    # Publish the run set only after every task produced a real result. Until this point the
    # checked-in evidence and summary remain a consistent prior snapshot.
    for task, output in outputs.items():
        (RUNS / f"{task}.txt").write_text(output)

    records.sort()
    grouped = defaultdict(list)
    for record in records:
        grouped[record[1]].append(record)
    lines = [f"Regenerated successfully: {len(records)}/{len(tasks)} tasks; 0 infrastructure errors.",
             f"Pinned task repository ref: {ref}", ""]
    for status in sorted(grouped):
        rows = grouped[status]
        clean = sum(not failures for _, _, failures in rows)
        clean_without_readme = sum(not [f for f in failures if f != "README sections"]
                                   for _, _, failures in rows)
        counts = Counter(failure for _, _, failures in rows for failure in failures)
        lines.append(f"== {status}: {len(rows)} tasks | 0 FAIL: {clean} | "
                     f"0 FAIL ignoring README-sections: {clean_without_readme}")
        lines.append(f"   FAIL: {dict(counts)}")
    lines += ["", "== tasks with FAIL:"]
    for task, status, failures in records:
        if failures:
            lines.append(f"   {task:56} {status:26} {failures}")
    (HERE / "presubmit-summary.txt").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
