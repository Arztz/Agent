---
name: orchestrate
description: "Route ALL tasks through the orchestrator agent. Use this for ANY user request - orchestrator will delegate to tech-lead. Trigger: /orchestrate"
allowed-tools: Agent
---

# Orchestrate — Route Tasks Through Orchestrator

Use this skill to ensure ALL user requests go through the orchestrator agent.

## Usage

```
/orchestrate [your task description]
```

## What This Does

1. Spawns the `orchestrator` agent with your task
2. Orchestrator analyzes the request
3. Orchestrator delegates to `tech-lead` only
4. Tech-lead coordinates execution through the team

## Examples

```
/orchestrate Build a login feature
/orchestrate Fix the bug in the payment module
/orchestrate Add unit tests for the API
```

## Flow

```
USER → /orchestrate → orchestrator → tech-lead → [team]
```

## Important

- **NEVER spawn agents directly** - always use this skill to route through orchestrator
- Orchestrator handles discovery, planning, and delegation
- Tech-lead executes through developer-lead, po, infra-lead, qa-lead, bu
