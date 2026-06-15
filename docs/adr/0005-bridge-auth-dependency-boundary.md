# ADR 0005: Bridge Auth Dependency Boundary

## Status

Accepted

## Date

2026-06-15

## Context

ADR 0004 introduced a responsibility-boundary policy for large Python modules. As part of that work, #173 attempted to split `src/sayane/bridge/app.py` into FastAPI route modules.

The initial staged route modules compiled, but rewiring was deferred because the Bridge authentication dependency was defined as a closure inside `create_app()`:

```python

def require_bearer(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    ...
```

This closure captured `cfg` and worked while all route definitions lived inside `create_app()`. However, moving routes across module boundaries exposed a FastAPI dependency-shape problem.

Several approaches were tested:

```text
1. APIRouter + include_router
2. direct route registration from another module
3. route registrar copying route definitions into another module
4. callable-instance dependency object
5. dependency factory using Header(default=None)
6. Request-based dependency factory
```

The early variants produced `422 Unprocessable Entity` because FastAPI treated dependency markers as request parameters rather than resolving the bearer-token dependency as intended.

A later test variant using:

```python
_: Annotated[None, Depends(require_bearer)] = None
```

removed the 422 but also allowed missing or invalid authentication to return `200`, meaning the dependency was not executed in that test shape.

The focused validation finally passed when authentication was expressed as route metadata:

```python
@app.get("/protected", dependencies=[Depends(require_bearer)])
def protected() -> dict[str, bool]:
    return {"ok": True}
```

Local validation result:

```text
python -m compileall src/sayane/bridge tests/test_bridge_auth_dependency.py
pytest tests/test_bridge_auth_dependency.py -q

3 passed in 0.29s
```

## Decision

Bridge authentication dependencies that exist only to authorize a route must be registered as route-level dependencies:

```python
@router.get("/path", dependencies=[Depends(require_bearer)])
def endpoint(...):
    ...
```

They must not be represented as dummy endpoint parameters such as:

```python
_: Annotated[None, Depends(require_bearer)]
```

or:

```python
_: Annotated[None, Depends(require_bearer)] = None
```

The Bridge auth dependency should be exposed through a module-level factory:

```python
require_bearer = create_bearer_dependency(cfg)
```

The dependency implementation should avoid fragile header-parameter introspection when crossing module boundaries. The accepted implementation reads the `Authorization` header from `Request` and delegates token validation to existing token verification logic.

## Rationale

Authentication is route metadata, not endpoint business input. Treating it as a dummy endpoint parameter creates two risks:

1. FastAPI may treat the marker as a missing request parameter and return `422`.
2. Adding a default may make the route callable while failing to execute the dependency in some refactor shapes.

Route-level `dependencies=[Depends(...)]` expresses the intent directly:

```text
execute this dependency before the endpoint body
```

It also keeps endpoint signatures focused on request data that the endpoint actually consumes.

Using `Request` inside the dependency avoids dependency-shape drift caused by `Header(...)` interpretation across nested factories, callable objects, and route modules.

## Consequences

### Positive

- #173 route-module rewiring can resume with a stable auth dependency pattern.
- Auth behavior remains explicit at the route decorator level.
- Endpoint function signatures no longer contain unused auth-only parameters.
- Existing bearer-token error details can be preserved:

```text
401 Missing or invalid Authorization header
401 Invalid bearer token
```

### Negative

- Route modules must consistently remember to attach `dependencies=[Depends(require_bearer)]` to protected endpoints.
- Authentication is less visible in the function parameter list, though more visible in route metadata.
- Existing staged route modules must be revised before #173 rewiring if they currently use dummy dependency parameters.

## Required Pattern

Protected Bridge route modules should follow this pattern:

```python
from fastapi import APIRouter, Depends


def register_example_routes(app, cfg, require_bearer):
    router = APIRouter()

    @router.get("/example", dependencies=[Depends(require_bearer)])
    def get_example() -> dict:
        return {"ok": True}

    app.include_router(router)
```

If the endpoint requires request body, path, or query parameters, those remain normal function parameters. The auth dependency stays in route metadata.

## Rejected Patterns

### Dummy required dependency parameter

```python
def endpoint(_: Annotated[None, Depends(require_bearer)]) -> dict:
    ...
```

Rejected because it can be interpreted as a required request parameter, causing `422`.

### Dummy optional dependency parameter

```python
def endpoint(_: Annotated[None, Depends(require_bearer)] = None) -> dict:
    ...
```

Rejected because local validation showed missing and invalid auth returning `200` in the focused test, indicating the dependency was not enforcing auth in that shape.

### Callable-instance dependency as primary pattern

```python
Depends(BearerTokenAuth(cfg))
```

Rejected as the primary pattern because callable-instance inspection proved fragile in the tested environment.

## Scope

This ADR applies to Sayane Local Bridge FastAPI route modules.

It does not apply to:

- CLI commands
- MCP stdio operations
- non-HTTP service-layer authorization
- candidate lifecycle semantics
- `candidate_api.py` internals

## Validation

Focused validation for the accepted pattern:

```bash
python -m compileall src/sayane/bridge tests/test_bridge_auth_dependency.py
pytest tests/test_bridge_auth_dependency.py -q
```

Expected result:

```text
3 passed
```

Before closing #173, run:

```bash
python -m compileall src/sayane/bridge
pytest
```

## RDE Note

The intended meaning delta is:

```text
HTTP auth dependency boundary clarification
```

This ADR must not change:

- bearer token validation semantics
- HTTP status codes
- HTTP error detail strings
- endpoint URLs
- HTTP methods
- request or response payload shape
- candidate lifecycle behavior

Any such change is behavior drift, not refactor noise.
