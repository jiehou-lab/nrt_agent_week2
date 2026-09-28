# Realistic histology MCP + permissions demo

Recommended image:

```text
data/case_mild_injury_histology.pgm
```

Color preview:

```text
previews/case_mild_injury_histology.png
```

Recommended parameters:

```text
magnification = 20
damage_threshold_fraction = 0.45
```

## Terminal

```bash
cd tissue_analyzer_mcp_realistic_permissions_*
claude
```

Inside Claude Code:

```text
/mcp
/permissions
```

Confirm:
- MCP server: `tissue-analyzer`
- direct `Read(./data/**)` is denied
- `Bash` is denied for this project

## Test direct access

```text
Read data/case_mild_injury_histology.pgm directly and summarize the raw pixels.
```

That path should be blocked by the project permission rule.

## Test approved MCP path

```text
Use the tissue-analyzer MCP tool analyze_tissue with:

slide = data/case_mild_injury_histology.pgm
magnification = 20
damage_threshold_fraction = 0.45
out = results/mild_permission_analysis.json
```

Then classify:

```text
Use classify_tissue with:

features = results/mild_permission_analysis.json
out = results/mild_permission_classification.json
```

## Teaching point

```text
Claude direct Read/Bash  ----X----> raw image

Claude
  |
  +--> MCP tool --> local analysis code --> raw image
                                   |
                                   +--> structured result
```

This demonstrates a **Claude Code permission boundary**, not OS-level isolation.
