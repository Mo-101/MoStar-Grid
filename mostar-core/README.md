# MoStar Core Kernel — Sprint 1

This repository contains the foundation kernel of MoStar, built around the paradigm that **MoStar is not the FGrid; it is a native, specialized entity living inside it.** 

FGrid operates as the universal knowledge fabric containing all entities (users, tasks, projects, codebases, and assistants) and relationships (owns, pursued, protected, etc.). MoStar operates as an `Executive Intelligence` node that traverses and updates this graph.

## Architecture & Structure

```
mostar-core/
├── pyproject.toml           # Package configuration
├── core/
│   ├── fgrid/               # FGrid Base schemas and in-memory graph
│   │   ├── models.py        # Entity, Relationship, MoStarEntity, CognitionState
│   │   └── graph.py         # FGrid Graph traversal engine
│   ├── soul/                # Immutable kernel identity, mission, and values
│   │   ├── identity.py
│   │   ├── mission.py
│   │   ├── values.py
│   │   └── version.py
│   ├── runtime/             # Executive Cortex tick event loop
│   │   └── runtime.py
│
├── services/
│   ├── personas/            # Persona managers and YAML configurations
│   │   ├── manager.py
│   │   └── personas/
│   │       ├── prime.yaml
│   │       ├── woo.yaml
│   │       ├── architect.yaml
│   │       └── sentinel.yaml
│   ├── memory/              # FGrid-grounded memory stores
│   │   ├── working.py       # Focus context & interaction logs
│   │   ├── personal.py      # User details & preferences
│   │   ├── project.py       # Projects and active tasks
│   │   └── vault.py         # Private keys and secure configs
│   └── planner/             # Graph-traversal based planner
│       └── planner.py
│
├── api/                     # FastAPI endpoint definitions
│   ├── main.py
│   └── routes.py
│
└── tests/                   # Automated pytest suite
```

## Running the API Server

Start the API server via Uvicorn from the `mostar-core` folder:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 41010 --reload
```

Then visit the Swagger documentation at: `http://localhost:41010/docs`

### Key Endpoints

- `POST /api/command`: Dispatches a command to a specific persona (e.g., `Prime`, `Woo`, `Architect`, `Sentinel`) and logs the interaction in working memory.
- `GET /api/fgrid/entities`: Lists all currently loaded entities in the FGrid.
- `POST /api/fgrid/entities`: Registers a new node in the graph.
- `POST /api/fgrid/relationships`: Adds a new edge between nodes.
- `POST /api/runtime/tick`: Triggers a manual tick of the Executive Cortex (evaluates pending tasks, creates plans, and advances them).

## Running Tests

Run the test suite using pytest:

```bash
pytest -v tests/
```
