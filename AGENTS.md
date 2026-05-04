# PI Agent System

This is a multi-agent orchestration system for software development. The root orchestrator delegates to tech-lead who coordinates all execution.

## Agent Hierarchy

```
orchestrator (Level 0)
└── tech-lead (Level 1) - Coordinator, task creator, reports to orchestrator
    ├── developer-lead (Level 2) - Technical execution lead
    │   ├── backend-lead → backend-senior → [backend-junior-a, backend-junior-b]
    │   ├── frontend-lead → frontend-senior → [frontend-junior-a, frontend-junior-b]
    │   └── ux-ui-lead → [ux-senior, ui-senior]
    ├── po (Level 2) - Product owner
    │   └── ba-senior → [ba-junior-a, ba-junior-b]
    ├── infra-lead (Level 2) - Infrastructure lead
    │   ├── devops-lead → devops-senior
    │   ├── sre-lead → [sre-senior, app-support]
    │   ├── dba-lead → [dba-senior-a, dba-senior-b]
    │   └── cloud-engineer-lead → cloud-engineer-senior
    ├── qa-lead (Level 2) - QA lead
    │   └── qa-senior → [qa-tester-a, qa-tester-b]
    └── bu (Level 2) - Business unit
        ├── business-strategy
        ├── bi-lead → bi-developer-senior
        ├── data-analysis-lead → data-analyst-senior
        └── knowledge-manager
```

## Entry Point (CRITICAL)

**ALL user input goes to orchestrator FIRST. No other agent should respond directly to user.**

When you receive a user request:
1. YOU (orchestrator) handle it
2. Delegate to tech-lead only
3. Sub-agents (qa-lead, developer-lead, etc.) should NEVER be spawned directly by user input - only via tech-lead

```
USER → orchestrator → tech-lead → [other agents]
     ↑ NEVER: user → qa-lead (WRONG)
```

## Delegation Rules (CRITICAL)

1. **orchestrator → tech-lead only** (never skip to developer-lead or others)
2. **tech-lead → developer-lead, po, infra-lead, qa-lead, bu** (direct reports)
3. **All leads → seniors → juniors** (respect chain, never skip levels)
4. **Parallel allowed**: Different Level-2 leads can work simultaneously
5. **Never bypass hierarchy**: tech-lead → developer-lead, NOT tech-lead → backend-senior

## Agent Definitions

Each agent is defined in a separate markdown file (e.g., `backend-junior-a.md`). These files include:
- Role persona and operational domain
- Step-by-step invocation process
- Detailed checklists for quality standards
- JSON communication protocol schemas

## Communication Protocol

See `DELEGATION-PROTOCOL.md` for shared protocols on:
- Task creation (todo tool)
- File locking ([LOCK]/[UNLOCK])
- Status updates
- Blocker escalation
- Sync points

## Navigation

- `team.json` — current agent hierarchy and relationships
- `DELEGATION-PROTOCOL.md` — shared coordination protocols
- `settings.json` — tracks OpenCode version
- `.opencode/memory/project.md` — project-specific memory

## Behavioral Guidelines

### 1. Think Before Coding
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.

### 2. Simplicity First
- Minimum code that solves the problem. Nothing speculative.
- If you write 200 lines and it could be 50, rewrite it.

### 3. Surgical Changes
- Touch only what you must. Match existing style.
- Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution
- Define success criteria. Loop until verified.
- Write tests first, then make them pass.