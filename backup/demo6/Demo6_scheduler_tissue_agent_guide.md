# Step-by-step guide — a job that outlives the conversation

Package:

`Demo6_scheduler_tissue_agent.zip`

Everything so far finished inside a single turn. Real research does not. A
simulation runs for three days; a batch of a thousand slides runs overnight; the
queue alone can be longer than your afternoon.

This demo submits the same tissue analysis to a scheduler and never waits for it.

```text
agent -> submit_job    -> scheduler       (an id comes back immediately)
         ...the work happens in a process nobody is waiting for...
agent -> check_status  -> queued / running / completed
agent -> get_results   -> a report you then have to read properly
```

**No cluster is required.** The default backend is a local simulator, so the whole
pattern runs on a laptop with nothing but Python 3. Part E swaps it for real
Slurm, one environment variable.

---

## 1. Unzip and look at the shape

```bash
unzip Demo6_scheduler_tissue_agent.zip
cd Demo6_scheduler_tissue_agent
ls -R | head -30
cat .claude/settings.json
```

Four tools, and no shell:

```text
submit_job     queue work, return an id, do not wait
check_status   where has that id got to
get_results    the report, once there is one
list_jobs      everything submitted from this folder
```

```bash
cat scheduler/backend.py | head -30
```

One file knows whether this is a laptop or a cluster. Everything above it —
`server.py`, `CLAUDE.md`, the agent — is identical either way.

Optional, to see the queue more clearly during the demo:

```bash
export TISSUE_FAKE_QUEUE_SECONDS=20
export TISSUE_FAKE_SECONDS_PER_SLIDE=3
```

---



# Part A — Submit, and watch nothing wait

## 2. Start Claude Code

```bash
claude
```

Choose **Use this MCP server** at the trust prompt, then confirm:

```text
/mcp
```

You should see `tissue-scheduler` with four tools.

## 3. Submit all eight slides

```text
Submit a batch job analyzing every slide in data/ at magnification 20
with damage_threshold_fraction 0.45.
```

Expected: an answer within a second or two, containing a job id.

```json
{
  "job_id": "job_1a2b3c4d",
  "state": "queued",
  "n_slides": 8,
  "note": "submitted and returned immediately - the work has NOT been done yet."
}
```

**Nothing has been analyzed yet.** The tool returned before the work started, on
purpose. Write the job id down.

## 4. Prove the job is not holding your session

While it is still queued or running, ask something completely unrelated:

```text
What does damage_threshold_fraction mean, and what happens if I pass 50?
```

You get an answer straight away. The job is not in your conversation; it is a
process on the machine, and your session is free.

```text
Now check on that job.
```

```json
{"job_id": "job_1a2b3c4d", "state": "running", "slides_done": 3, "slides_total": 8}
```

## 5. Ask for the results too early

```text
Get the results for that job now.
```

```json
{
  "error": "results are not ready",
  "state": "running",
  "hint": "call check_status until state is 'completed'"
}
```

Read what the agent does with that. The correct behaviour is to relay it and
stop. If instead it starts polling in a loop, or tells you it will "wait and
check back", that is the failure this demo exists to show: **an agent that waits
is an agent that has stopped being useful**, and on a three-day job it is an agent
that has died of a closed laptop.

---



# Part B — The job outlives the conversation

## 6. Leave

```text
/exit
```

Wait a few seconds. Start a completely new session:

```bash
claude
```

```text
What is the status of job_1a2b3c4d?
```

It answers. A different conversation, no shared memory, no context carried over —
and the job is exactly where it should be, because the state was never in the
conversation. It was in `jobs/job_1a2b3c4d/job.json` the whole time.

```bash
ls jobs/
cat jobs/job_1a2b3c4d/job.json
```

> This is the design rule: **anything that must survive belongs outside the
> agent.** A job id is a handle a human can carry between sessions, machines and
> months. A context window is not.

---



# Part C — Read the report properly

## 7. Fetch it

```text
Get the results for job_1a2b3c4d.
```

The `summary` line reads something like:

```text
8 slides analyzed. mean damage_fraction 0.263.
classifications: mild_injury x2, necrosis x3, normal x3.
```

Tidy. Quotable. It would go straight into an email.

## 8. Now count what it did not say

```text
How many of those slides came back with low_confidence true? Name them.
```

Then check for yourself:

```bash
python3 - <<'PY'
import json, glob
r = json.load(open(glob.glob("jobs/job_*/results.json")[0]))
print(r["summary"])
flagged = [s for s in r["slides"] if s["low_confidence"]]
print("flagged:", len(flagged), [s["slide"] for s in flagged])
PY
```

Three of the eight come back flagged, including the fold-artifact slide at
`confidence` 0.55 and `hard_edge_rate` 0.17 — and the summary never mentioned any
of them. They were averaged into `mean damage_fraction` alongside the five slides
the measurement was sure about.

This is the Demo 4 gap, at batch scale. One slide is a question you might catch.
Eight hundred slides is a number nobody checks — and the fraction flagged here,
three in eight, is not unusual for real data.

## 9. Find who decided

```bash
grep -n "def make_summary" -A 15 scheduler/runner.py
```

The summary is one function, fifteen lines, and it never looks at
`low_confidence`. Nothing failed. Nobody lied. The report simply reflects what
its author thought was worth saying.

## 10. Fix it

Edit `make_summary` in `scheduler/runner.py` so the line it returns states how
many slides were flagged and refuses to be quoted without them. Then submit the
same eight slides again and compare the two reports.

```text
Submit the same eight slides again with the same parameters.
```

Reports are not neutral. Someone chooses their summary statistics, and that
choice is as much a part of the method as the threshold.

---



# Part D — Permissions, with consequences attached

## 11. Try to reach the scheduler directly

```text
Run `squeue -u $USER` to check the queue.
```

Denied — `.claude/settings.json` has no `Bash` at all. Also try:

```text
Read data/case_001.pgm and show me the header.
```

Also denied.

## 12. Say why that is different here

On a laptop, denying `Bash` is a teaching exercise. On a shared cluster, an agent
with a shell can `scancel` an array that belongs to somebody else, fill a scratch
quota, or turn one mistyped loop into five hundred queued jobs charged to a real
allocation.

```text
Demo 3   deny rules    kept an agent away from one folder
Demo 6   deny rules    keep an agent away from shared infrastructure
```

Four tools that do exactly four things is not a restriction on capability. It is
the reason this is safe to point at a queue at all.

---



# Part E — Point it at a real cluster

## 13. Switch the backend

```bash
export TISSUE_SCHEDULER=slurm
```

Nothing else in the project changes. `scheduler/backend.py` now shells out to
`sbatch --parsable` and reads state from `squeue`, falling back to `sacct` once a
job leaves the queue.

## 14. Fill in your site's details

```bash
cat slurm/job_template.sbatch
```

Account, partition and module lines are commented out because they differ at
every institution. On MSU's HPCC you will need at minimum an `--account` and
whatever `module load` gives you Python 3.

```bash
cat scheduler/slurm_worker.py
```

That is the body of the job — the same analysis, without the simulated queue,
writing `results.json` in the same shape so nothing above `backend.py` notices
which scheduler ran it.

> **Not tested on a cluster by the course staff.** Every site differs in
> partitions, modules, filesystem layout and job-accounting policy. Treat this as
> a starting point, read it before you run it, and test with one slide before you
> submit eight hundred.

## 15. Three things to check before you trust it on real work

```text
1. Does the job land in the right account, with a time limit you meant?
2. Does the worker see the same filesystem paths the submitting host used?
3. When a job fails, does check_status say 'failed' - or does it silently
   report 'unknown' and let the agent claim success?
```

Number 3 is the one that bites. A status mapping that turns an unrecognised
scheduler state into something reassuring is exactly the fold artifact again,
wearing different clothes.

---



## Appendix — what a job directory is worth

```bash
ls jobs/job_1a2b3c4d/
```

```text
job.json                      parameters, timestamps, state history
case_001_analyze.json         per-slide measurements
case_001_classify.json        per-slide labels
results.json                  the report, with every input recorded
```

Nobody designed this as a provenance system, but that is what it is. Six months
from now the question "what did we actually run?" has an answer that does not
depend on anyone remembering a conversation.

An agent's chat log is not a method section. A job directory can be.
