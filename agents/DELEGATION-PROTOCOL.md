# DELEGATION-PROTOCOL.md

**Shared protocols for ALL PI agents. Every agent must follow these rules.**

---

## 1. TASK MANAGEMENT (todo tool)

### Creating Tasks (tech-lead only)
```javascript
// Create a task with owner and dependencies
todo create:
  subject: "Task name"
  description: "What to do"
  owner: "assigned-agent"
  blockedBy: [task_id]  // optional, for dependencies
  status: pending
```

### Updating Task Status
```javascript
todo update:
  id: task_number
  status: in_progress | completed | pending
  owner: "agent-name"
  activeForm: "currently doing..."
```

### Checking Task Status
```javascript
// Before starting work, check if blocked
todo list  // shows all tasks with blockedBy

// If your task is blocked by another, wait until it's completed
// Only proceed when: blockedBy = [] or all blocking tasks = completed
```

### Task Dependency Pattern
```
Task A (owner: agent-X) ──┐
                           ├──> Task C (owner: agent-Z) 
Task B (owner: agent-Y) ──┘

Task C has: blockedBy: [A, B]
Both A and B must complete before C can start
```

---

## 2. FILE LOCKING PROTOCOL

### Before Writing ANY File
```javascript
// Step 1: Announce lock
Print: "[LOCK] /path/to/file.ts by your-name"

// Step 2: Write the file
write content to file

// Step 3: Announce unlock
Print: "[UNLOCK] /path/to/file.ts by your-name"
```

### Lock Announcement Examples
```
[LOCK] src/api/auth.ts by backend-senior
[LOCK] src/components/Dashboard.tsx by frontend-lead
[UNLOCK] src/api/auth.ts by backend-senior
```

### Rules
- **ONE agent owns ONE file at a time**
- If another agent needs the same file, wait for unlock
- Read the file before writing (to get latest changes)
- Never overwrite another agent's changes without coordination

### Conflict Detection
```javascript
// If you try to read a file and find [LOCK] marker from another agent:
// 1. Wait
// 2. Try again after unlock
// 3. Or escalate to your parent agent
```

---

## 3. STATUS REPORTING

### Report to Parent (After Task Completion)
```javascript
// Pattern: Report up the chain
Print: "✅ Task #N completed by [your-name]"
Print: "📤 Reporting to [parent-agent]"
```

### Report Blocker (Escalation Pattern)
```javascript
// Junior hits blocker
Print: "⚠️ BLOCKER: Cannot access [resource]"
Print: "📤 Escalating to [parent-agent]"
Print: "⏳ Waiting for resolution..."
```

### Orchestrator Report (tech-lead only)
```javascript
// tech-lead reports to orchestrator
Print: "📊 STATUS UPDATE:"
Print: "- Tasks completed: X"
Print: "- Tasks in progress: Y"
Print: "- Blocked tasks: Z"
Print: "- Blocker escalation: [list]"
```

---

## 4. HIERARCHICAL DELEGATION RULES

### The Chain (NEVER skip levels)
```
Level 0: orchestrator
    └── Level 1: tech-lead (only agent orchestrator talks to)
        └── Level 2: developer-lead, po, infra-lead, qa-lead
            └── Level 3: leads (backend-lead, frontend-lead, etc.)
                └── Level 4: seniors
                    └── Level 5: juniors
```

### Correct Delegation ✅
```
orchestrator → tech-lead
tech-lead → developer-lead
developer-lead → backend-lead
backend-lead → backend-senior
backend-senior → backend-junior-a
```

### WRONG - Skip Levels ❌
```
orchestrator → developer-lead  // WRONG - skip tech-lead
tech-lead → backend-senior      // WRONG - skip developer-lead
tech-lead → backend-junior-a    // WRONG - skip 2 levels
```

### Parallel Execution (Allowed)
- tech-lead can delegate to multiple Level-2 agents simultaneously
- Different seniors can work on different files in parallel
- Different juniors can work on different files in parallel

---

## 5. INTER-AGENT SYNC POINTS

### Sync Point: Before Starting Dependent Work
```javascript
// Agent waiting for another agent's output
1. Check todo list
2. If blockedBy tasks are completed → proceed
3. If not completed → announce waiting, try again later

Example:
Print: "[WAITING] Task #5 not completed, checking again..."
Read: file-from-task-5
Print: "✅ Task #5 completed, proceeding with implementation"
```

### Communication Pattern
```javascript
// Agent A creates output
write file
Print: "[UNLOCK] file.ts by agent-a"

// Agent B reads output
Read file
Print: "[LOCK] file.ts by agent-b"
// ... do work ...
Print: "[UNLOCK] file.ts by agent-b"
```

---

## 6. BLOCKER ESCALATION CHAIN

### When You Hit a Blocker
```javascript
// Step 1: Identify blocker
Print: "⚠️ BLOCKER: [What is blocked]"
Print: "   Reason: [Why]"

// Step 2: Try to resolve yourself (junior/senior only)
Print: "   Attempting self-resolution..."

// Step 3: If cannot resolve, escalate
Print: "📤 ESCALATING to [parent-agent]"
Print: "   Issue: [Detailed description]"
Print: "   Needed: [What would fix it]"

// Step 4: Wait for parent response
Print: "⏳ Waiting for [parent-agent] to resolve..."
```

### Escalation Path
```
backend-junior-a → backend-senior → backend-lead → developer-lead → tech-lead → orchestrator
```

---

## 7. TASK COMPLETION PATTERN

### Standard Completion
```javascript
// 1. Update todo status
todo update id: N status: completed

// 2. Unlock any locked files
Print: "[UNLOCK] file.ts by your-name"

// 3. Report to parent
Print: "✅ Task #N ([title]) completed by [your-name]"
Print: "📤 Reporting to [parent-agent]"

// 4. Request next task (if applicable)
Print: "🎯 Ready for next task from [parent-agent]"
```

---

## 8. FILE OWNERSHIP MAP

### Maintain (mentally or in notes)
```javascript
file_ownership = {
  "src/api/auth.ts": "backend-senior",
  "src/components/Button.tsx": "frontend-lead",
  "src/config/db.ts": "infra-lead",
  // ... etc
}
```

### Before Assigning Work
- Check if file is already owned
- If not owned → assign to the agent who will work on it
- If owned → wait for owner to complete OR assign to same agent

---

## QUICK REFERENCE CARD

| Action | Command |
|--------|---------|
| Create task | `todo create` with subject, owner, blockedBy |
| Start task | `todo update` status: in_progress |
| Complete task | `todo update` status: completed |
| Lock file | Print `[LOCK] path by agent` |
| Unlock file | Print `[UNLOCK] path by agent` |
| Check status | `todo list` |
| Report to parent | Print status + "📤 Reporting to [parent]" |
| Escalate blocker | Print "⚠️ BLOCKER" + "📤 ESCALATING to [parent]" |

---

## ENFORCEMENT

**All agents MUST follow these protocols. Violations:**
- Skipping hierarchy levels → reject and redirect
- File conflicts → stop, report, wait for resolution
- Not using todo → task not tracked, completion not verified

**This protocol is the single source of truth for agent coordination.**