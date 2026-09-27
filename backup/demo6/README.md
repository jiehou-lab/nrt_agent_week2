# Demo 6 — parked, not deleted

Scheduled batch agent: `submit_job` / `check_status` / `get_results` / `list_jobs`,
with a local simulator so it runs on a laptop and a Slurm backend behind
`TISSUE_SCHEDULER=slurm`.

Taken off the site on 2026-09-27 because the walkthrough was not yet easy enough
to follow unaided. The package itself is tested: submit returns immediately,
states go queued -> running -> completed, and the report's summary omits the
three slides flagged `low_confidence` (which is the lesson).

## What is here

    demo6.html                                  the rendered guide page
    Demo6_scheduler_tissue_agent.zip            the package (41 files)
    Demo6_scheduler_tissue_agent_guide.md       the guide source

## To put it back

1. `mv demo6.html ../../guides/`
2. `mv Demo6_scheduler_tissue_agent.zip ../../downloads/`
3. In `advanced.html`: restore the Demo 6 level card and the "caution about the
   cluster path" section, and put the Level 3 row in the table back.
4. In `guides/demo5.html`: change the bottom nav's first button back to
   `demo6.html` — "Next: Demo 6 →".
5. In `index.html`: the pointer note above the setup section says "One more, for
   later"; make it two again.

## What to fix first, if you rewrite it

The guide asks the reader to hold several new ideas at once: an asynchronous
tool, a job id that survives a session, a summary that lies by omission, and a
scheduler they may never have used. Splitting it would help — one short demo
that only submits and polls, and a separate one about reading the report.
