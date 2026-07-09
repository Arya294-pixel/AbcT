# abct/emit/cpp/include.py
from __future__ import annotations
import re
import json
from pathlib import Path
from typing import Any, List, Union

# for Clarity
from abct.abct_ast.node import (Node, Call, TemplateCall,
    BinOp, Attribute, Name, AnnAssign)
from abct.abct_ast.node import * # to avoid Errors
from .types import ann_to_cpp

# 1. System headers hardcoded - these always exist
SYSTEM_HEADER_MAP = {
    "std::int8_t": ("cstdint", True),
    "std::int16_t": ("cstdint", True),
    "std::int32_t": ("cstdint", True),
    "std::int64_t": ("cstdint", True),
    "std::uint8_t": ("cstdint", True),
    "std::uint16_t": ("cstdint", True),
    "std::uint32_t": ("cstdint", True),
    "std::uint64_t": ("cstdint", True),
    "std::string": ("string", True),
    "std::cout": ("iostream", True),
    "std::endl": ("iostream", True),
}

# Core internal headers that the compiler provides
CORE_HEADER_MAP = {
    "CompileTimeConst": ("abct/AbcTTypes.hpp", False),
}

USER_HEADER_MAP = {
    "print": ("AbcTIO.hpp", False),
    "input": ("AbcTIO.hpp", False),
}

# 2. Load user/project headers from JSON
try:
    user_site = Path("~/.config/abct/include.json").expanduser()
    if user_site.is_file():
        with open(user_site) as f:
            data = json.load(f)
            USER_HEADER_MAP.update({k: tuple(v) for k, v in data.items()})
except Exception:
    pass

# Load project-local overrides
jsonfile = Path(__file__).parent / "include.json"
if jsonfile.is_file():
    with open(jsonfile) as f:
        USER_HEADER_MAP.update({k: tuple(v) for k, v in json.load(f).items()})

# 3. Final map: Core > User > System (Core overrides all)
HEADER_MAP = {**SYSTEM_HEADER_MAP, **USER_HEADER_MAP, **CORE_HEADER_MAP}

class IncludeCollector:
    def __init__(self):
        self.headers: set[tuple[str, bool]] = {
            ("abct/AbcTRuntime.hpp", True)
        }

    def visit(self, node: Node):
        if isinstance(node, (tuple, list)):
            for items in node:
                self.visit(items)

        match node:
            case Name(id=id):
                self._check_func(id)

            case AnnAssign(annotation=ann, value=value):
                self._check_type(ann_to_cpp(ann))
                if value:
                    self.visit(value)

            case FuncDef(body=body):
                self.visit(body)

            case Expr(value=value):
                self.visit(value)

            case If(test=test, body=body, orelse=orelse):
                self.visit(test)
                self.visit(body)
                self.visit(orelse)

            case Call(func=func, args=args):
                self.visit(func)
                if isinstance(func, Attribute):
                    func = func.attr
                self._check_func(func, args)
                for arg in args:
                    self.visit(arg)

            case TemplateCall(func=Attribute(value=Name(id=mod), attr=attr), targs=targs, args=args):
                self._check_func(f"{mod}::{attr}", args)
                for t in targs: self._check_type(t)
                for a in args: self.visit(a)

            case TemplateCall(func=Name(id=f), targs=targs, args=args):
                self._check_func(f, args)
                for t in targs: self._check_type(t)
                for a in args: self.visit(a)

            case ClassDef(public_attributes=pub_attrs, private_attributes=priv_attrs,
                          public_methods=pub_methods, private_methods=priv_methods):
                self.visit(pub_attrs)
                self.visit(priv_attrs)
                self.visit(pub_methods)
                self.visit(priv_methods)

            case BinOp(op="Pow", left=l, right=r):
                self._check_func("pow", [])
                self.visit(l)
                self.visit(r)

            case BinOp(left=l, right=r):
                self.visit(l)
                self.visit(r)

            case _:
                pass

    def _check_func(self, name: any, args=None):
        if hasattr(name, "id"):
            name = name.id
        elif hasattr(name, "attr"):
            name = name.attr

        if not isinstance(name, str):
            return

        key = f"std::{name}" if not name.startswith("std::") else name
        if key in HEADER_MAP:
            self.headers.add(HEADER_MAP[key])

        if name != key and name in HEADER_MAP:
            self.headers.add(HEADER_MAP[name])

    def _check_type(self, t: str):
        ts = self.extract_qualified_names(t)
        if not ts:
            ts = [t]
        for t in ts:
            if t in HEADER_MAP:
                self.headers.add(HEADER_MAP[t])

    def render(self) -> list[str]:
        lines = []
        for header, system in sorted(self.headers):
            if system:
                lines.append(f"#include <{header}>")
            else:
                lines.append(f'#include "{header}"')
        return list(set(lines))

    @staticmethod
    def extract_qualified_names(s: str) -> set[str]:
        # Regex captures both single IDs (CompileTimeConst) and qualified IDs (std::vector)
        return set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*', s))
