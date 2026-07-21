# dagster-workshop-multi

A multi-container introduction to [Dagster](https://dagster.io) using the
real production pattern: one Docker container per pipeline, each running its
own Dagster gRPC code server, registered with a central webserver/daemon via
`workspace.yaml`.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Internet access (both pipelines call free public APIs)

## Quickstart

```bash
docker compose up --build
```

Then open http://localhost:3000. Under Deployment > Code Locations you should
see `pipeline_products` and `pipeline_fx`, each its own container. Select all
assets and click "Materialize all" to run both pipelines end to end.

## What just happened

```
                     dagster_webserver (:3000)  <-- workspace.yaml -->  dagster_daemon
                              |                                              |
                              +---------------------+-----------------------+
                                                     |
                             dagster_postgresql  (Dagster's own run/schedule/event storage)

  pipeline_products (:4000)                    pipeline_fx (:4001)
  fakestoreapi.com -> raw_products/raw_orders   api.frankfurter.app -> raw_exchange_rates
        |                                              |
        v                                              v
  products, orders tables  ------------------->  warehouse_postgresql  <-------  exchange_rates table
```

Each pipeline is a fully independent container: its own `Dockerfile`, its own
`requirements.txt`, its own source/db modules. They only share the
`warehouse_postgresql` database as a landing zone — exactly like production's
21 pipeline containers, each pulling from its own source system into one
destination database.

Both pipelines write with a simple truncate-and-load (`if_exists="replace"`)
— a simplified stand-in for production's shift-based "check-then-insert"
pattern.

## Exercises

See [docs/exercises.md](docs/exercises.md) for three hands-on TODOs, in
increasing difficulty. Each one has a `# TODO(exercise-N)` comment marking
where to add your code.

## How this maps to the production pipeline

This is adapted from a real Dagster + Docker production system with 21
pipeline containers pulling manufacturing data (OEE, downtime, QC) from
internal MSSQL/AS400 systems into a central SQL Server database. This
workshop keeps the core architecture — one container per pipeline, gRPC code
servers, `workspace.yaml` registration, a shared destination database — but
swaps the internal systems for free public APIs, and drops production's
`DockerRunLauncher` (which spawns a fresh container per run via a mounted
`docker.sock`) in favor of Dagster's default run launcher, where runs execute
in-process within each pipeline's own gRPC container. See
`dagster-workshop-basic` for a single-container introduction to the core
Dagster concepts before diving into this multi-container version.
