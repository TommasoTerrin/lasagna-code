#!/bin/bash
# Shared scaffold for lasagna eval cases. Sourced by each case's fixture.sh,
# which runs in the empty run workspace (only with `claude plugin eval --scaffold`).
#
#   . "$(dirname "$0")/../_lib/project.sh"
#   shop_project            # a tiny Python project with code and tests
#   lasagna_init            # .lasagna/ with a v2 profile, empty architecture
#   phase_state <phase> <active_role>
set -eu

shop_project() {
  mkdir -p src/shop tests
  cat > src/shop/__init__.py <<'EOF'
EOF
  cat > src/shop/cart.py <<'EOF'
MAX_ITEMS = 50


def cart_total(prices):
    """Total of a cart, in cents."""
    total = 0
    for p in prices[1:]:
        total += p
    return total
EOF
  cat > tests/test_cart.py <<'EOF'
from shop.cart import cart_total


def test_empty_cart_costs_nothing():
    assert cart_total([]) == 0
EOF
  cat > pyproject.toml <<'EOF'
[tool.pytest.ini_options]
pythonpath = ["src"]
EOF
  git init -q && git add -A && git -c user.email=e@x -c user.name=eval commit -qm init
}

lasagna_init() {
  mkdir -p .lasagna/specs/archive .lasagna/contracts .lasagna/state docs/context
  cat > .lasagna/stack.md <<'EOF'
language: python
test_command: python -m pytest -q
test_command_pattern: (pytest|python -m pytest)
fail_compile_pattern: (ModuleNotFoundError|ImportError|SyntaxError|NameError)
fail_assert_pattern: (AssertionError|^E +assert)
fail_generic_pattern: ([0-9]+ failed|[0-9]+ error|FAILED|ERROR)
pass_pattern: ([0-9]+ passed|no tests ran)
test_path: tests/
test_file_pattern: (^|/)tests?/|(^|/)test_[^/]*\.py$|conftest\.py$
source_path: src/
budget_core: 3
budget_shell: 5
budget_bugfix: 5
context_dir: docs/context
EOF
  printf '# Architecture\n\nlevel:\norigin:\nconfirmed_by:\n' > .lasagna/architecture.md
  printf '# Project context — index\n\n| Context | What it is | File |\n|---|---|---|\n' > docs/context/INDEX.md
  printf '.lasagna/state/\n' >> .gitignore
}

# A small FastAPI-style service with conventions of its own: logic in
# app/services, a DomainError hierarchy mapped to HTTP in main.py, repositories
# passed in as parameters, an in-memory fake in the tests. No ports/adapters.
fastapi_project() {
  mkdir -p app/services tests
  : > app/__init__.py
  : > app/services/__init__.py
  cat > app/errors.py <<'EOF'
class DomainError(Exception):
    status_code = 400


class NotFound(DomainError):
    status_code = 404


class InvalidState(DomainError):
    status_code = 409
EOF
  cat > app/repositories.py <<'EOF'
class OrderRepository:
    """SQL-backed in production; tests use FakeOrderRepository."""

    def __init__(self, session):
        self.session = session

    def get(self, order_id):
        return self.session.get("orders", order_id)

    def save(self, order):
        self.session.put("orders", order["id"], order)
EOF
  cat > app/services/orders.py <<'EOF'
from app.errors import InvalidState, NotFound


def confirm_order(repo, order_id):
    order = repo.get(order_id)
    if order is None:
        raise NotFound(f"order {order_id}")
    if order["status"] != "pending":
        raise InvalidState(f"order {order_id} is {order['status']}")
    order["status"] = "confirmed"
    repo.save(order)
    return order
EOF
  cat > app/main.py <<'EOF'
from fastapi import FastAPI, HTTPException

from app.errors import DomainError
from app.repositories import OrderRepository
from app.services import orders

app = FastAPI()


def get_repo():
    return OrderRepository(session=app.state.session)


@app.post("/orders/{order_id}/confirm")
def confirm(order_id: str):
    try:
        return orders.confirm_order(get_repo(), order_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
EOF
  cat > tests/test_orders.py <<'EOF'
import pytest

from app.errors import InvalidState
from app.services.orders import confirm_order


class FakeOrderRepository:
    def __init__(self, *orders):
        self.orders = {o["id"]: o for o in orders}

    def get(self, order_id):
        return self.orders.get(order_id)

    def save(self, order):
        self.orders[order["id"]] = order


def test_pending_order_is_confirmed():
    repo = FakeOrderRepository({"id": "1", "status": "pending"})
    assert confirm_order(repo, "1")["status"] == "confirmed"


def test_confirmed_order_cannot_be_confirmed_again():
    repo = FakeOrderRepository({"id": "1", "status": "confirmed"})
    with pytest.raises(InvalidState):
        confirm_order(repo, "1")
EOF
  git init -q && git add -A && git -c user.email=e@x -c user.name=eval commit -qm init
}

# An approved feature with a frozen contract, ready for tdd-loop.
approved_feature() {
  printf 'level: minimal\norigin: greenfield\nconfirmed_by: eval\n\nCore: src/shop/ (pure functions). No shell yet.\n' > .lasagna/architecture.md
  cat > .lasagna/specs/FEAT-001.md <<'EOF'
# Spec — FEAT-001: correct cart total

feature_id: FEAT-001
flow: official
status: approved
approved_by: eval on 2026-10-07
contexts: none

## Goal

`cart_total` returns the sum of all prices, and refuses negative prices.

## Acceptance criteria

| ID | Given | When | Then |
|---|---|---|---|
| AC-FEAT-001-001 | prices [10, 20] | cart_total is called | it returns 30 |
| AC-FEAT-001-002 | prices [10, -5] | cart_total is called | it raises ValueError |

## Slices

| Slice | Criteria | Touches the outside world? |
|---|---|---|
| S1 | AC-FEAT-001-001, AC-FEAT-001-002 | no |
EOF
  cat > .lasagna/contracts/FEAT-001.md <<'EOF'
# Frozen interface contract — FEAT-001

frozen_on: 2026-10-07
approved_by: eval

## Seams under test

`shop.cart.cart_total` — the only public function.

## Signatures

```python
def cart_total(prices: list[int]) -> int: ...
```

## Error types

| Error | When | Spec code |
|---|---|---|
| `ValueError` | any price is negative | AC-FEAT-001-002 |

## Return shape

Exceptions for errors; the total in cents on success.

## External dependencies

None: pure function.

## What is NOT frozen

The loop, helper functions.
EOF
  cat > .lasagna/state/FEAT-001.state.md <<'EOF'
feature_id: FEAT-001
flow: official
phase: tdd-loop
layer: core
current_slice: S1: AC-FEAT-001-001, AC-FEAT-001-002
contexts: none
budget_max:
cycles_used: 0
active_role: none
last_test_result: none
escalation: none

## Criteria

AC-FEAT-001-001: open
AC-FEAT-001-002: open

## Checkpoint

## Cycle log

| when | role | outcome |
|---|---|---|
EOF
}

# phase_state <phase> <active_role>: an approved feature in progress.
phase_state() {
  cat > .lasagna/specs/FEAT-001.md <<'EOF'
# Spec — FEAT-001: cart total
feature_id: FEAT-001
status: approved
| AC-FEAT-001-001 | a cart with prices [10, 20] | the total is computed | it is 30 |
EOF
  cat > .lasagna/contracts/FEAT-001.md <<'EOF'
# Frozen interface contract — FEAT-001
approved_by: eval
def cart_total(prices: list[int]) -> int: ...
EOF
  cat > .lasagna/state/FEAT-001.state.md <<EOF
feature_id: FEAT-001
flow: official
phase: $1
layer: core
current_slice: S1: AC-FEAT-001-001
budget_max: 3
cycles_used: 0
active_role: $2
last_test_result: red-assertion
escalation: none

## Checkpoint

## Cycle log

| when | role | outcome |
|---|---|---|
EOF
}
