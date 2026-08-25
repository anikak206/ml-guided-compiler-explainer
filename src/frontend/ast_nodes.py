"""
Phase 2b: AST Node Definitions
--------------------------------
Every node has a `line` field, because we need to trace optimizations
back to source lines later. This is non-negotiable for our project's
whole premise (LLM explanations tied to source lines).

Each class here is just a labeled bundle of data - no behavior.
The parser's job (in parser.py) is to construct these into a tree.
"""

from dataclasses import dataclass, field


@dataclass
class Num:
    value: int
    line: int


@dataclass
class Ident:
    name: str
    line: int


@dataclass
class BinOp:
    op: str        # '+', '-', '*', '/', '<', '>', '=='
    left: object    # another Num / Ident / BinOp
    right: object
    line: int


@dataclass
class VarDecl:
    name: str
    init: object   # expression, or None if no initializer (e.g. `int n;`)
    line: int


@dataclass
class Assign:
    name: str
    value: object   # expression
    line: int


@dataclass
class If:
    condition: object   # BinOp
    body: list          # list of statements
    line: int


@dataclass
class For:
    init: object      # VarDecl or Assign
    condition: object  # BinOp
    step: object       # Assign
    body: list         # list of statements
    line: int


@dataclass
class Return:
    value: object   # expression
    line: int


@dataclass
class Program:
    body: list = field(default_factory=list)  # top-level statements inside main()