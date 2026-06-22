# Resident Daemon Overview Preview

This document records the first app-facing `daemon-overview` slice.

## Status

`daemon-overview` is implemented as a future-UI-oriented aggregate preview.

## Scope

The payload combines:

- daemon lifecycle status
- liveness diagnostic preview
- readiness diagnostic preview
- runtime initialization preview
- cleanup preview summary
- repair preview summary
- suggested next commands

## Purpose

The overview gives future resident UI code one stable, non-mutating payload instead of requiring
multiple command-specific fetches just to render the current local daemon situation.

## Evidence boundary

The overview is still derived preview data.

It does not:

- prove process identity
- prove daemon readiness
- prove API readiness
- authorize mutation
- authorize process control

## Non-goals

This slice does not add:

- GUI framework code
- tray UI
- background polling
- persisted dashboard state
- mutation batching
