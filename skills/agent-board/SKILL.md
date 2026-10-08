---
name: agent-board
description: A live, plain-language web page that shows which agent (Claude Code sessions, subagents, Codex, people) owns which job, what each is doing right now, how far along every job is, and what is waiting on the user. Use it when two or more agents split a plan and the user wants to SEE it ("show me who is doing what", "make a board for the agents", "/agent-board"), AND whenever you are a helper on a plan that has a board: you report your progress to it. Builds one private claude.ai Artifact with a shared database, registers every session by its tab title, and keeps it current.
---

# Agent Board

A dashboard for work split between several agents. One card per helper (its tab
title, a status badge, "Right now: ..." in one plain sentence, its jobs with
progress bars), a table of every job, four summary numbers, and a yellow
"Needs your attention" box listing what is waiting on the person.

The page is a claude.ai Artifact whose data lives in the Artifact's shared
database. Agents report by WRITING ROWS with the `ArtifactData` tool; the page
updates live. Nobody has to read messages to know where things stand.

Files next to this one:
- `board.html` — the page template. Never hand-write a new page; copy this.
- `scripts/session_titles.py` — lists running Claude Code sessions with the
  title shown on each session's tab.

## Which role am I?

- **Helper**: someone sent you a board link, or your project instructions or
  memory name an active board. Follow **Helper** below. Do it without being
  reminded: a board that lags reality is worse than no board.
- **Coordinator**: the user asked for a board, or asked you to split work
  between agents. Follow **Coordinator**.

## Writing rules (both roles)

Everything a person reads on the board is written for someone who does not
know the codebase.
- `plain` and `title` fields: everyday words, one sentence or a short phrase.
  No commit hashes, ticket codes, file names, or jargon. "Making backups also
  save the keys needed to restore", not "Phase 5 key escrow (a1b2c3)".
- Technical detail goes in `doing`, `detail`, `next`, `blocker`. The page does
  not show `doing` when `plain` is set.
- `asks` on the person's row: one sentence per decision, starting with a verb.

## Coordinator

1. **Find or create the board.** `Artifact` `action: "list"`; reuse a page
   titled `<Project> Agent Board` if one exists. Otherwise copy `board.html`
   to your scratchpad, change only `<title>`, and publish with
   `capabilities: {"db": {}, "user": {}}`, `icon: "board"`, and a one-sentence
   `description`.
2. **Find the helpers.** `ListAgents` gives the addresses.
   `python3 <skill dir>/scripts/session_titles.py --cwd <repo>` gives each
   session's tab title (`title`, null when the session has none). Pick short
   path-safe ids (the session name's last segment works: `b5`, `aa`). Add
   rows for non-Claude helpers (`kind: "codex"`) and for the person
   (`kind: "human"`, with `asks`). Add yourself, `role: "coordinator"`.
3. **Seed** everything in one `ArtifactData` `batch` (schema below). Use
   your best estimate for `progress` and tell helpers to correct it.
4. **Make it stick.** Helpers forget messages; they do not forget their
   project instructions. Write this block where every session of the project
   reads it at start: the project's auto-memory index if the harness has one,
   otherwise `CLAUDE.local.md` in the repository root. Ask before editing a
   checked-in `CLAUDE.md`.

   ```
   ## Agent Board
   A live board tracks who does what: <url>
   If you own or help on a job there, update your rows (agent-board skill,
   "Helper") whenever your state changes: when you start, reach a milestone,
   get blocked, need the user, or finish. Write `plain` in everyday words.
   ```
5. **Invite every helper** with one `SendMessage` each, first line
   `Agent Board: please report your progress at <url>`, then: their agent id,
   the job ids they own or help on, and "Follow the agent-board skill's
   Helper section." If the skill may not be installed on their side, include
   the three Helper writes below verbatim.
6. **Keep it current.**
   - When a helper reports to YOU instead of the board, write it for them.
   - Helpers that cannot write (Codex, people, other tools): you update their rows.
   - When something starts or stops waiting on the person, update their `asks`.
   - Reassigning a job: change its `owner` and both helpers' `plain` in one batch.
   - A card marked "No update for ..." means that helper went quiet: ask it.
   - Hand the person the link once. Afterwards, say only what changed.

## Helper

Load the tool once: `ToolSearch` with `select:ArtifactData`.

Report at every state change: you start a job, reach a milestone, get
blocked or unblocked, need the person, finish a job, or go idle. In ONE
`ArtifactData` `batch`:

1. `update` `tasks/<job-id>`: `status`, `progress` (0-100), `next`,
   `blocker` (remove with `{"__delete__": true}`), `updated_at` (ISO time),
   `updated_by` (your id).
2. `update` `agents/<your-id>`: `state`, `plain` (one everyday sentence:
   what you are doing right now), `doing`, `updated_at`.
3. If the person must decide something, tell the coordinator; it owns `asks`.

Read each document first (`get`) and pass its `version` as `if_version`. If a
write is refused because the version moved, read again and redo it. Write only
your own agent row and jobs you own or help on. Never delete rows.

## Data schema

| Document | Fields |
|---|---|
| `meta/board` | `title`, `plain` (subtitle in everyday words) |
| `agents/<id>` | `name` (the address, e.g. `myrepo-b5`), `title` (tab title), `label` (short name, e.g. `Claude b5`), `kind` (`claude`/`codex`/`human`/`other`), `role` (a few everyday words), `state` (`working`/`waiting`/`blocked`/`idle`/`offline`), `plain`, `doing`, `asks` (person only: list of sentences), `n` (sort order), `updated_at` |
| `tasks/<id>` | `plain` (the job in everyday words, about 8 words), `title`, `detail`, `owner` (agent id), `helpers` (agent ids), `status` (`todo`/`doing`/`blocked`/`review`/`done`), `progress` (0-100), `next`, `blocker`, `n`, `updated_at`, `updated_by` |

Status words on the page: `todo` Not started, `doing` Working on it, `review`
Almost done, `blocked` Waiting, `done` Done. A helper whose `state` is
`working` with no update for 45 minutes shows "No update for ...".

## Verify once

After the first publish and seed: one `ArtifactData` `list` of `agents` and
`tasks`, then give the person the link. No render loops.

## Limits

- The board is private to its owner until shared from the page's Share menu.
- Sessions only see the board if they run on the same claude.ai account.
- A held cross-session message needs the person's approval in that session's
  window; the board itself never needs approval to read.
