---
description: Analyze one tissue slide through the MCP tool
argument-hint: <slide_path> <magnification> <damage_threshold_fraction>
---

Use the `tissue-analyzer` MCP server.

Interpret `$ARGUMENTS` as:

1. slide path
2. magnification
3. damage_threshold_fraction

Always save the measurement result to:

`results/<case>_permission_analysis.json`

Do not read the `.pgm` file directly and do not invoke Python scripts through Bash.
Return only the MCP tool result.
