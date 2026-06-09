# abct/emit/common/expr.py
from __future__ import annotations
from abct.abct_ast.node import *
from abc import ABC

class CAndCppCommonExpr(ABC):
    """Shared expr logic. Default to clean C-style names. C++ overrides only if needed."""

    def emit_expr(self, node: Node) -> str:
        match node:
            case Const(value=v):
                return self.emit_const(v)
            case Name(id=i):
                return i
            case Attribute(value=v, attr=attr):
                return self.emit_attribute(v, attr)
            case BinOp(left=l, op=op, right=r):
                return self.emit_binop(l, op, r)
            case Compare(left=l, op=op, right=r):
                return f"({self.emit_expr(l)} {self.cmp_op(op)} {self.emit_expr(r)})"
            case UnaryOp(op=op, operand=o):
                return f"{self.unary_op(op)}{self.emit_expr(o)}"
            case Call(func=f, args=args, keywords=[]):
                return self.emit_call(f, args)
            case TemplateCall(func=f, targs=targs, args=args, keywords=[]):
                return self.emit_template_call(f, targs, args)
            case _:
                raise NotImplementedError(f"{type(self).__name__}: {type(node).__name__}")

    # ---- Identical in C and C++ ----
    def bin_op(self, op: str) -> str:
        return {"Add":"+","Sub":"-","Mult":"*","Div":"/","Mod":"%"}[op]

    def cmp_op(self, op: str) -> str:
        return {"Eq":"==","NotEq":"!=","Lt":"<","LtE":"<=","Gt":">","GtE":">="}[op]

    def unary_op(self, op: str) -> str:
        return {"UAdd":"+","USub":"-","Not":"!","Invert":"~"}[op]

    def emit_call(self, func: Node, args: list) -> str:
        args_s = ", ".join(self.emit_expr(a) for a in args)
        return f"{self.emit_expr(func)}({args_s})"

    def emit_binop(self, l: Node, op: str, r: Node) -> str:
        if op == "Pow":
            return self.emit_pow(l, r)
        if op == "FloorDiv":
            return self.emit_floordiv(l, r)
        return f"({self.emit_expr(l)} {self.bin_op(op)} {self.emit_expr(r)})"

    def emit_pow(self, l: Node, r: Node) -> str:
        # Default: unqualified. Both C and C++ allow this with <cmath>/<math.h>
        return f"pow({self.emit_expr(l)}, {self.emit_expr(r)})"

    def emit_floordiv(self, l: Node, r: Node) -> str:
        return f"({self.emit_expr(l)} / {self.emit_expr(r)})"

    # ---- Must diverge: raise ----
    def emit_const(self, v) -> str:
        raise NotImplementedError(f"{type(self).__name__} must override emit_const")

    def emit_attribute(self, value: Node, attr: str) -> str:
        raise NotImplementedError(f"{type(self).__name__} must override emit_attribute")

    def emit_template_call(self, func: Node, targs: list, args: list) -> str:
        raise NotImplementedError(f"{type(self).__name__} must override emit_template_call")
