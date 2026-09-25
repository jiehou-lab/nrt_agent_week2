# Realistic histology MCP + scoped subagent demo

Recommended cases:

```text
data/case_normal_histology.pgm
data/case_mild_injury_histology.pgm
data/case_necrosis_histology.pgm
data/case_fold_artifact_histology.pgm
```

Matching color previews are in:

```text
previews/
```

## Start Claude Code

```bash
cd tissue_analyzer_mcp_realistic_subagent_*
claude
```

Inside Claude Code:

```text
/mcp
```

Confirm that `tissue-analyzer` is connected.

## Test normal delegation

```text
Use the tissue-analyst subagent to analyze
data/case_mild_injury_histology.pgm
with magnification 20 and damage_threshold_fraction 0.45.
```

The intended chain is:

```text
main Claude agent
   ↓
tissue-analyst subagent
   ↓
analyze_tissue MCP
   ↓
classify_tissue MCP
   ↓
structured result
   ↓
main Claude agent
```

## Try the project command

```text
/analyze-slide data/case_necrosis_histology.pgm
```

## Test the tool boundary

```text
Use tissue-analyst to directly open
data/case_mild_injury_histology.pgm
and print its raw pixel values.
```

The scoped subagent should not have a generic `Read` tool.

## Useful artifact case

```text
/analyze-slide data/case_fold_artifact_histology.pgm
```

This case is useful because it can produce a plausible class while also
showing elevated edge/artifact information. It demonstrates that:

```text
valid structured output != equally trustworthy scientific output
```

## Teaching point

Subagent scoping answers:

> Which capabilities can this specialized agent call?

It does not by itself answer:

> What can the entire Claude Code session or operating system access?
