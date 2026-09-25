# Two versions of the same subagent

| File | Difference |
|---|---|
| `v1_has_a_gap.md` | stops when `usable` is false — and nothing else. **This is what the package ships with.** |
| `v2_checks_confidence.md` | also checks `low_confidence`, and leads the report with it |

The fold-artifact case returns `usable: true` and `low_confidence: true`. Version 1
checks only the first, so it reports `mild_injury` at probability 0.7 with no
warning at all — the same output it gives for a genuinely mild case.

Swap a version in with:

```bash
cp docs/subagent_versions/v2_checks_confidence.md .claude/agents/tissue-analyst.md
```

then restart Claude Code and run the fold case again.

The point is not that version 1 was carelessly written. It checks a field that
sounds like the right one. **The gap is between a rule that sounds correct and a
rule that covers the case you actually care about** — and the only way to find it
is to run the hard case and read the output.
