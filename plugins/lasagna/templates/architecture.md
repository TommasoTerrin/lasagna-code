# Architecture — <project>

File: `.lasagna/architecture.md`. Committed. Written by `grilling` (greenfield)
or `reverse-spec-brownfield` (existing code), confirmed by a human. Read by
domain-modeling, freeze-contract, the implementer and the adversarial reviewer.
**No hook reads it**: everything here is guidance and review material, never a
mechanical check.

confirmed_by: <human name> on <YYYY-MM-DD>
origin: greenfield | detected

## Separation level

level: minimal | modular | full-hexagonal

Why this level, in two or three lines. What would make it worth moving up or
down a level later.

| Level | When | Shape |
|---|---|---|
| minimal | little business logic: scripts, simple CRUD | one pure logic module + the edges |
| modular | non-trivial logic, some external dependencies (recommended default) | modules per feature, a pure core per module, a `Protocol`/interface only on the dependencies that earn one |
| full-hexagonal | complex domain, several real adapters for the same port, strong consistency constraints | explicit ports and adapters, aggregates |

## Where core and shell live

- **Core** (pure: data in, data out — no I/O, clock, randomness, environment):
  `<paths>`
- **Shell** (endpoints, CLI, jobs, database, files, network — thin, few `if`s):
  `<paths>`

## Libraries allowed in the core

Standard library plus: `<e.g. pydantic>`. Anything else enters through the shell.

## Conventions

On an existing codebase these are **detected and followed**, even where they
differ from lasagna's preferences. Proposals to change them go to
`.lasagna/design-notes.md`, never straight into the code.

| Topic | Convention | Example in the code |
|---|---|---|
| Errors | exceptions / result types / error codes | `<file:line>` |
| Dependency injection | parameters / constructor / container / module globals | |
| Tests | framework, layout, fixtures, test doubles in use | |
| Folder structure | by feature / by technical layer | |
| Naming | | |

## Abstractions (`Protocol` / interface)

Used only when one of these holds: the technology may really change; the test
must replace something slow or non-deterministic; two implementations already
exist. Otherwise pass a value or a function.

| Abstraction | Why it exists | Implementations |
|---|---|---|
| | | |
