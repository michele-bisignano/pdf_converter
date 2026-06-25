# Architecture Decisions

> Decide weird way add entry. Drop alternative add entry. Stop repeat talk.

## Entry Format

```
## [YYYY-MM-DD] Decision Title
- Context: Why decide.
- Decision: What pick.
- Dropped: What drop. Why drop.
- Impact: Known effect. Accept trade-off.
```

---

<!-- Example. Drop write real. -->

## [2026-01-15] Example: Pick memory format
- **Context**: Need save project context Claude Code sessions.
- **Decision**: Pick markdown files (CLAUDE.md + memory/).
- **Dropped**: Graphiti need big setup. Vector DB waste tokens. Project too small.
- **Impact**: Require manual file update. Save tokens. Drop external dependency.