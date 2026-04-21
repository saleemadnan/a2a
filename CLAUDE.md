# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent2Agent (A2A) is an open protocol by Google that enables interoperability between AI agents built on different frameworks. The repository contains the protocol specification, Python and JavaScript sample implementations, a web demo, protocol compliance tests, and documentation.

## Commands

### Python formatting (runs on files changed vs `origin/main`)
```bash
nox -s format
```
This runs pyupgrade → autoflake → ruff check --fix-only → ruff format in sequence. Requires Python 3.11.

### Python linting only (without auto-fix)
```bash
ruff check samples/python/
ruff format --check samples/python/
```

### Run all protocol compliance tests
```bash
cd tests && uv run pytest -v -s
```

### Run a single test file
```bash
cd tests && uv run pytest -v -s test_a2a_spec.py
```

### Reset test environment after changing `samples/python/common/`
```bash
cd tests && uv clean && rm -rf .pytest_cache .venv __pycache__ && uv run pytest -v -s
```

### JavaScript agents (from `samples/js/`)
```bash
pnpm install
pnpm agents:movie-agent   # runs movie-agent sample
pnpm agents:coder         # runs coder agent sample
pnpm a2a:cli              # runs CLI client
```

### Build and serve documentation locally
```bash
pip install -r requirements-docs.txt
mkdocs serve
```

## Architecture

### Protocol Layer
The canonical protocol definition is `specification/json/a2a.json` (JSON Schema Draft 7). All Pydantic models in `samples/python/common/types.py` must conform to this schema. The tests in `tests/test_a2a_spec.py` validate sample messages against it using `jsonschema`.

### Core Data Model (in `types.py`)
- **AgentCard** — agent metadata served at `/.well-known/agent.json`; describes name, skills, capabilities, and authentication requirements
- **Task** — the central work unit; identified by a unique string ID; transitions through states: `submitted → working → input-required | completed | failed | canceled`
- **Message** — exchanged between user/agent roles; contains one or more **Part** items
- **Part** — atomic content unit: `TextPart`, `FilePart`, or `DataPart`
- **Artifact** — task output (generated content, files, structured data)

### Python Common Library (`samples/python/common/`)
This is the reusable library (`a2a-samples` package) that all Python agents and hosts import:

- **`client/client.py`** — `A2AClient`: sends JSON-RPC requests, handles SSE streaming, polls task state
- **`client/card_resolver.py`** — `A2ACardResolver`: discovers an agent's `AgentCard` via HTTP GET to `/.well-known/agent.json`
- **`server/server.py`** — `A2AServer`: Starlette-based HTTP server; routes JSON-RPC method names to `TaskManager` callbacks; returns `EventSourceResponse` for streaming methods
- **`server/task_manager.py`** — `TaskManager` abstract base class; concrete agents implement `on_send_task` and `on_send_task_subscribe`
- **`types.py`** — all Pydantic v2 models and type aliases; `A2ARequest` is a discriminated union used for request deserialization

### Transport and Protocol
- Transport: HTTP/HTTPS
- Message format: JSON-RPC 2.0
- Streaming: Server-Sent Events via `tasks/sendSubscribe`
- Async/webhooks: push notifications (`tasks/pushNotification/set`, `tasks/pushNotification/get`)
- Authentication is declared in AgentCard (OpenAPI security schemes) and passed out-of-band via HTTP headers

### Agent Samples (`samples/python/agents/`)
Each subdirectory is a separate UV workspace member with its own `pyproject.toml`. Each agent:
1. Defines an `AgentCard` with its skills and capabilities
2. Implements a `TaskManager` subclass containing the agent logic
3. Starts an `A2AServer` instance

Available framework examples: `google_adk`, `langgraph`, `crewai`, `llama_index_file_chat`, `marvin`, `mindsdb`, `semantickernel`, `ag2`.

### Host Applications (`samples/python/hosts/`)
- **`cli/`** — interactive CLI that takes a server URL, resolves its AgentCard, and sends tasks
- **`multiagent/`** — orchestrator agent (Google ADK) that routes requests to remote A2A agents

### Web Demo (`demo/ui/`)
Mesop-based web app (`main.py` entry point) that visualizes multi-agent conversations, task history, and supports dynamic agent discovery. Its own `pyproject.toml` requires Python 3.12+.

### JavaScript Samples (`samples/js/`)
TypeScript implementations using Genkit + Express. Uses `pnpm` as the package manager (v10.7.1).

## Code Style

### Python
- Follows **Google Python Style Guide**
- Line length: **80 characters**, indent: **4 spaces**
- Single quotes for inline strings, double quotes for docstrings
- Absolute imports only (relative imports are banned by ruff `TID` rules)
- Google-style docstrings (`pydocstyle` convention)
- Target: Python 3.11+ (samples), 3.12+ (tests and demo)
- All formatting is enforced by ruff (config in `.ruff.toml`)

### JavaScript/TypeScript
- Prettier enforced: tab width 2, trailing commas ES5, bracket same line

## UV Workspace Structure

`samples/python/pyproject.toml` declares a UV workspace. The `a2a-samples` package (built from `common/` and `hosts/`) is shared across all workspace members. When making changes to `common/`, other members pick them up automatically within the workspace but the `tests/` directory (a separate UV project) needs a cache clear.

## CI/CD (`.github/workflows/`)

| Workflow | Trigger | Scope |
|----------|---------|-------|
| `linter.yaml` | PRs and pushes (not main) | `docs/` and `specification/` only |
| `spelling.yaml` | All branches and PRs | Spell-check with auto-fix bot |
| `docs.yml` | Push to main | MkDocs build → GitHub Pages |
| `links.yaml` | Daily + manual | Lychee broken-link check |

Note: Python linting (ruff/black/flake8) is **not** run in CI — format locally with `nox -s format` before committing.
