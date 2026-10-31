# {{PRODUCT_NAME}}: Architecture

Last updated by {{LATEST_CR}}.

## Context

Who and what the system talks to.

```mermaid
{{CONTEXT_DIAGRAM}}
```

## Components

```mermaid
{{COMPONENT_DIAGRAM}}
```

| Component | Responsibility | Code |
|---|---|---|
{{COMPONENT_TABLE}}

## Data model
{{DATA_MODEL}}

## Integrations and adapters
External services sit behind adapters so they can be mocked in tests and demos and swapped for real ones later.

| Integration | Adapter | Current mode | To go live |
|---|---|---|---|
{{INTEGRATIONS_TABLE}}

## Key flows
{{FLOWS}}

## Quality attributes
Performance, security, privacy and accessibility choices, and how they are verified.
{{QUALITY}}

## Decisions
See [../adr/](../adr/). The most important so far:
{{ADR_LIST}}
