---
name: flux-compare
description: "Compare FluxCD environment overlays (develop/uat/prod) for apps, clusters, infrastructure, operator, or dependencies. Supports resource comparison (patch.yaml) and ENV comparison (secrets.yaml) with colorized table output."
---

# Flux Compare - Environment Overlay Comparison Tool

## Overview

This skill compares FluxCD environment overlays across `develop`, `uat`, and `prod` environments to identify:
1. **Resource differences** in `patch.yaml` files (replicas, resources, etc.)
2. **ENV key coverage** in `secrets.yaml` files (prod ≥ uat ≥ dev pattern validation + alphabetical sorting)

## Usage

```
/flux-compare apps|clusters|dependencies|infrastructure|operator [resource|env|both]
```

### Examples

```bash
/flux-compare apps resource    # Compare patch.yaml resources for all apps
/flux-compare infra env        # Compare ENV keys in infrastructure secrets
/flux-compare apps both         # Compare both resource and ENV (default)
/flux-compare operator both    # Compare operator overlays
```

## Architecture

### Core Components

```
flux-compare/
├── parser/
│   ├── yaml_parser.py       # Parse patch.yaml and secrets.yaml
│   ├── path_resolver.py     # Resolve service paths by type
│   └── diff_engine.py       # Compare values and detect issues
├── formatters/
│   ├── table_formatter.py   # ASCII table with colors
│   └── report_generator.py  # Generate summary reports
└── (main logic in SKILL.md)
```

### Path Resolution by Type

| Type | Base Path | Environment Subdirs |
|------|-----------|---------------------|
| `apps` | `apps/base/{service}/` | `apps/{develop,uat,prod}/{service}/` |
| `clusters` | `clusters/base/` | `clusters/{develop,uat,prod}/` |
| `infrastructure` | `infrastructure/base/` | `infrastructure/{nonprod,uat,prod}/` |
| `operator` | `operator/base/` | `operator/{nonprod,uat,prod}/` |
| `dependencies` | `dependencies/base/` | `dependencies/{develop,uat,prod}/` |

### Key Comparisons

#### 1. Resource Comparison (patch.yaml)

**Critical resources only:**
- `spec.values.deployment.replicaCount`
- `spec.values.resources.limits.cpu|memory`
- `spec.values.resources.requests.cpu|memory`
- `spec.values.autoscaling.minReplicas|maxReplicas` (if enabled)

**Excluded:**
- Image tags (always different per environment)
- Ingress hosts/paths (environment-specific)
- env vars in patch.yaml (use secrets.yaml ENV instead)

#### 2. ENV Comparison (secrets.yaml)

Compare the **keys** (not values) in `stringData`:
- Extract all key names from each environment's secrets.yaml
- Check coverage: `prod_keys ⊇ uat_keys ⊇ dev_keys`
- Detect missing keys in higher environments
- Validate alphabetical sorting after separator

## ENV Structure Pattern (secrets.yaml)

All secrets.yaml files MUST follow this structure:

```yaml
stringData:
    #-----------------Default ENV----------------------#
    SERVICE_NAME: {value}     # Key only, value irrelevant
    ENV: {value}              # Key only, value irrelevant
    VERSION: {value}           # Key only, value irrelevant
    HTTP_BASE_PATH: {value}   # Key only, value irrelevant
    HTTP_SERVER_PORT: {value} # Key only, value irrelevant
    DB_NAME: {value}          # Key only, value irrelevant
    #--------------------------------------------------#
    [all other ENV keys alphabetically sorted]
```

**Rules:**
1. First section: 6 required "Default ENV" **keys** (values ignored - SOPS encrypted)
2. Second section: Everything else alphabetically sorted (A-Z)
3. The `#--------------------------------------------------#` separator marks the boundary

**Comparison:**
- Extract all **keys** (values are SOPS encrypted - ignored)
- Split into: `default_keys` (6 fixed) + `sorted_keys` (alphabetical rest)
- Validate: dev/uat/prod should have identical key sets

## Auto-Fix: Interactive (Service by Service)

For ENV key sorting issues:
1. **Report phase**: Scan all services, identify which need fixing
2. **Fix phase**: Ask user service by service:
   ```
   Service: agent-service
   Issues found:
   - ENV keys not alphabetically sorted after separator
   - 2 missing keys in dev that exist in uat/prod
   
   Fix now? [y/N/q(quit)]:
   ```
3. **Per-service fix**: Show proposed changes, ask for confirmation, then apply
4. **Batch mode**: Option to skip all and generate a fix script instead

## Output Format

### Resource Table

For **visual comparison**, each service shows 5 resource lines with DEV | UAT | PROD values:

```
┌─────────────────────┬──────────────────────────────────────────────────────────────┐
│ Service             │ Resource Comparison (DEV | UAT | PROD)                        │
├─────────────────────┼──────────────────────────────────────────────────────────────┤
│ agent-service       │ replicas: 2 | 1 | 2                                           │
│                     │ requests.cpu: 64m | 64m | 64m                                 │
│                     │ requests.ram: 128Mi | 128Mi | 256Mi ←highlighted               │
│                     │ limits.cpu: 128m | 128m | 128m                                 │
│                     │ limits.ram: 256Mi | 256Mi | 512Mi ←highlighted                  │
├─────────────────────┼──────────────────────────────────────────────────────────────┤
│ auth-service        │ replicas: 1 | 1 | 2                                           │
│                     │ requests.cpu: 32m | 32m | 64m                                 │
│                     │ requests.ram: 64Mi | 64Mi | 128Mi                              │
│                     │ limits.cpu: 64m | 64m | 256m                                   │
│                     │ limits.ram: 128Mi | 128Mi | 512Mi                              │
└─────────────────────┴──────────────────────────────────────────────────────────────┘

Legend: ✅ all match  ⚠️ highlighted if differs
```

**Rules:**
- 5 lines per service: replicas, requests.cpu, requests.ram, limits.cpu, limits.ram
- Highlight (yellow) any value that differs across environments
- N/A shown if field doesn't exist

### ENV Comparison Output

For **standardization and fix**, show MISSING and DIFF only:

```
=== ENV SUMMARY ===
Services with issues: 35
  PROD diff from UAT: 50 keys missing
  UAT diff from DEV: 35 keys missing
  Unique keys: 25 across all

=== ENV DETAILS ===

Service: fund-service
  PROD diff from UAT:
    MISSING_IN_PROD: KEY_1
    MISSING_IN_PROD: KEY_2
    UNIQUE_IN_PROD: KEY_3
  UAT diff from DEV:
    MISSING_IN_UAT: KEY_X

Service: agent-service
  PROD diff from UAT:
    MISSING_IN_PROD: KEY_A
    UNIQUE_IN_PROD: KEY_B
```

**Rules:**
- Compare: PROD vs UAT, UAT vs DEV
- Show MISSING keys (exist in higher env, missing in lower)
- Show UNIQUE keys (exist only in one env)
- One key per line for clarity

### Color Scheme (ANSI)

| Color | Escape | Meaning |
|-------|--------|---------|
| Green | `\033[32m` | Matched/OK |
| Yellow | `\033[33m` | Different (warning) |
| Red | `\033[31m` | Invalid/missing (error) |
| Blue | `\033[34m` | Info/header |
| Reset | `\033[0m` | Reset formatting |

## Implementation Checklist

- [x] Parse YAML files (patch.yaml, secrets.yaml)
- [x] Resolve paths for all 5 types (apps, clusters, infra, operator, deps)
- [x] Extract resource fields from HelmRelease (5 fields)
- [x] Extract ENV keys from secrets.yaml stringData
- [x] Split default vs sorted ENV sections
- [x] Compare resource values (resource mode) - 5 lines format
- [x] Check key coverage + sorting (ENV mode) - MISSING/DIFF only
- [x] Generate colorized ASCII tables
- [x] Interactive fix: service by service
- [x] Support "both" mode with combined output
- [x] Highlight differing values in resource table
- [x] Service-by-service ENV details with one key per line
- [ ] ENV auto-fix: sort keys, add missing keys
- [ ] ENV fix: interactive service-by-service

## Files

```
flux-compare/
├── SKILL.md              # This file
├── flux_compare_main.py # Entry point for skill invocation
├── flux_compare.py       # Main class
├── parser/
│   ├── __init__.py
│   ├── yaml_parser.py   # YAML parsing
│   ├── path_resolver.py # Path resolution
│   └── diff_engine.py   # Comparison logic
└── formatters/
    ├── __init__.py
    └── table_formatter.py # Colorized output
```

## Invocation

### From pi skill system:
```
/flux-compare apps both
/flux-compare infra env
/flux-compare apps resource --fix
```

### Direct execution:
```bash
cd /home/rut/robowealth/devops/fluxcd/fundii-flux
python .opencode/skills/flux-compare/flux_compare.py apps both
python .opencode/skills/flux-compare/flux_compare.py infra env --fix
```

### Programmatic:
```python
from flux_compare_main import invoke, invoke_fix, invoke_script

result = invoke("apps both")  # Generate report
invoke_fix("apps")            # Interactive fix
script = invoke_script("apps") # Generate fix script
```

## Edge Cases

1. **Service missing from an environment**: Show as `N/A` in table
2. **secrets.yaml encrypted**: Skip value comparison, only compare keys
3. **patch.yaml has complex nested values**: Flatten with dot notation
4. **Empty environments**: Report as `EMPTY` or `N/A`
5. **Different key names in same semantic field**: Normalize before comparison
6. **Missing separator line**: Treat all keys as unsorted, report warning

## Design Decisions

### 1. Key-Only vs Value Comparison for Secrets
**Decision**: Only compare KEY existence for secrets.yaml
**Reason**: Secrets are SOPS-encrypted; we want to ensure all environments have the same configuration keys

### 2. Critical Resources Only
**Decision**: Focus on replicaCount, CPU, memory limits/requests
**Reason**: Most important for capacity planning and environment consistency

### 3. Interactive Fix (Not Auto-Fix)
**Decision**: Ask user confirmation service by service
**Reason**: Safer approach - user sees what will change before applying

### 4. Table Sorting
**Decision**: Sort by service name alphabetically, errors first
**Reason**: Easy to find issues, consistent output

### 5. Color Terminal Output
**Decision**: Use ANSI escape codes for color
**Reason**: Standard terminal support, no external dependencies
