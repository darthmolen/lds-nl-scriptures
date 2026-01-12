# Scripture Search Project

## Project Context

- **Project Name**: Scripture Search
- **Primary Language**: Python
- **Framework**: FastAPI
- **Repository**: lds-nl-scriptures

## Planning Protocol

### Directory Structure

Maintain these directories for planning artifacts:

```
planning/
├── backlog/            # Future work items and deferred tasks
├── in_progress/       # Active phase documents
└── completed/         # Finished phase documents with outcomes
```

### Pre-Task Requirements

Before executing any task:

1. Create a phase document in `planning/in_progress/` named `phase_[name]_[date].md`
2. Document the objective, approach, and success criteria
3. List all files expected to be modified
4. Identify dependencies and prerequisites

### Post-Task Requirements

After completing any task:

1. Update the phase document with actual outcomes
2. Move completed phase documents to `planning/completed/`
3. Document any deviations from the plan
4. Note lessons learned or issues encountered
5. **COMMIT**: All work must be committed with a descriptive message before moving to the next phase

### Backlog Management

When discovering work outside current scope:

1. Do not attempt to address it immediately
2. Create a backlog item in `planning/backlog/` with full context
3. Continue with current phase execution
4. Reference the backlog item in phase completion notes

## Commit Protocol

### Mandatory Commit Points

- After completing each phase
- Before switching to a different task
- After any significant refactoring
- Before planning mode discussions about architectural changes

### Commit Message Format

```
[PHASE] Brief description

- Specific change 1
- Specific change 2

Phase: planning/completed/phase_[name]_[date].md
```

## Mode Management

### Planning Mode Triggers

Enter planning mode when:

- User ends message with "this is a query not a mandate"
- User requests brainstorming or exploration
- Task complexity requires multi-phase breakdown
- Uncertainty exists about the correct approach

### Planning Mode Behavior

- Do NOT make code changes
- Do NOT execute commands that modify state
- Present options and tradeoffs
- Ask clarifying questions
- Exit planning mode ONLY to create planning/ or planning/backlog documents
- Immediately re-enter planning mode after creating planning documents
- Remain in planning mode until explicit approval to execute

### Execution Mode Behavior

- Follow the approved phase document
- Make incremental progress with frequent saves
- Update phase document progress markers
- Stop and return to planning if scope expands

## Skills and Tools

### Required Skills for This Project

- /using-superpowers: at any time, whenever the user wants to start planning, discussing code, etc.
- /super-powers:brainstorm: whenever the user wants to implement or discuss plans or any deep discussions
- /super-powers:execute-plan: whenever a plan needs to be started or executed
- /subagent-driven-development: whenever the user is starting execution. always parallelize.

### Skill Invocation

Always auto-detect skills by their key words, but allow the user to explicitly ask for skills at the same time.

Example: "Using the [skill-name] skill, implement..."

## Testing Protocol

### Log Locations

- Application logs: `logs/`
- Test output: `pytest` output
- Error logs: stderr/stdout

### Test-First Bug Fixes

When fixing bugs:

1. Write or identify the failing test first
2. Run tests to confirm failure
3. Implement the fix
4. Run tests iteratively until passing
5. Do not declare victory until tests pass in execution
6. Always verify that the tests are testing what the problem was
7. If its a complicated bug across components, use an integration style test, but never test mocks or stubs, use them as boundaries.

### Iteration Loop

Claude has direct access to these log paths. When debugging:

1. Read relevant logs directly
2. Identify root cause from log evidence
3. Propose fix with test verification
4. Execute and verify in single workflow

## Async Work Identification

When reviewing a phase plan, actively identify:

- Independent tasks that can run in parallel
- Tasks with no shared state dependencies
- Tasks that can be delegated to sub-agents

Mark async-eligible tasks in phase documents with `[ASYNC]` prefix.

## Context Management

### Fresh Context Indicators

Start a new context window when:

- Phase document is complete and committed
- Context has accumulated significant exploration/debugging noise
- Moving to a substantially different area of the codebase

### Context Handoff

When suggesting a new context:

1. Ensure all changes are committed
2. Update phase document with current state
3. Provide summary of next steps for fresh context
4. Reference specific phase document to load

## Artifact Preservation

### Screenshots and Diagrams

When producing visual artifacts during planning:

1. Save to `planning/artifacts/` with descriptive names
2. Reference in phase documents
3. Include date in filename

### Decision Records

Document significant decisions in phase documents:

- What was decided
- Why (alternatives considered)
- Implications for future work

## Architecture Decision Records (ADRs)

### When to Create an ADR

Create an ADR in `documentation/ADR/` when:

- Choosing between architectural approaches
- Adopting or abandoning a technology
- Establishing patterns that affect multiple components
- Making decisions that would be expensive to reverse
- Superseding a previous architectural decision

See [ADR_TEMPLATE.md](ADR_TEMPLATE.md) for the required format.

## Communication Preferences

### Response Style

- Lead with direct answers, then explain
- Use code examples over abstract descriptions
- Flag uncertainty explicitly
- Suggest alternatives when blocking issues arise

### Progress Updates

When executing multi-step tasks:

- Indicate current step clearly
- Report blockers immediately
- Summarize completed work before pausing

## Project-Specific Instructions

### Architecture Decisions

- pgvector in existing Postgres (no separate vector db)
- text-embedding-3-small for embeddings
- gpt-4o-mini for generation
- Scriptures: verse-level chunks with ±2 verse context
- Topical Guide: relational, not vector
- Come Follow Me: separate table, yearly refresh
- **Languages**: English and Spanish (multi-lingual)
- **Auth**: Azure Entra ID (private, may go public later)
- **API**: Python FastAPI

### Data Sources

- Scripture quads: PDF → Markdown (via pymupdf4llm, incremental by book)
- Topical Guide: Embedded in quad PDF (pages 1606-2187)
- Come Follow Me manuals: PDF → Markdown
- Raw PDFs in `content/raw/`, processed markdown in `content/processed/`

### Data Formats

- **TOON (Token-Oriented Object Notation):** Compact serialization format for 30-60% token savings on tabular data. Used for Claude Project uploads. See [documentation/TOON-FORMAT-SUMMARY.md](documentation/TOON-FORMAT-SUMMARY.md) for details.
- Pipeline: Source → JSON (`content/processed/`) → TOON (`content/transformed/`)

### Project Roadmap

See `planning/roadmap.md` for detailed phases.

### System Architecture

See [documentation/SYSTEM-ARCHITECTURE.md](documentation/SYSTEM-ARCHITECTURE.md) for schema and flow diagrams.

### Constraints

- Shoestring budget
- Already have Postgres, AKS, AI Foundry
- Prove concept, potentially donate to church
