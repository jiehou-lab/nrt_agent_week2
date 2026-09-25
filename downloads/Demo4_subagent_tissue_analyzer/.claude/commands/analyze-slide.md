---
description: Analyze and classify one slide using the scoped tissue-analyst subagent
argument-hint: <slide_path>
---

Delegate analysis of **$1** to the `tissue-analyst` subagent.

Unless the user supplies different values, use:

- magnification = 20
- damage_threshold_fraction = 0.45

The subagent must use the MCP tools rather than invoking Python scripts directly.

Return:
- damage fraction
- tissue tile count
- hard-edge rate
- confidence/usability information
- class
- probability
