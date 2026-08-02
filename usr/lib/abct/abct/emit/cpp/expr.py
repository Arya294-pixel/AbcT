# abct/emit/cpp/expr.py
from __future__ import annotations
from ..common.expr import CAndCppCommonExpr
from .utils import _resolvetype
from abct.abct_ast.node import *

class CppExprGen(CAndCppCommonExpr):
    def __init__(self, ctx={}):
        self.ctx = ctx
    def emit_expr(self, node:Node):
        match node:
            case Attribute():
                return self.emit_attribute(node)
            case Array():
                return self.emit_array(node)
            case Subscript():
                return self.emit_subscript(node)
            case Call(func=func, args=args):
                func_name = emit_expr(func)
                cpp_args = [emit_expr(arg) for arg in node.args]
                return f"{func_name}({', '.join(cpp_args)})"

            case TemplateCall(func=func, targs=targs, args=args):
                return self.emit_template_call(func=func, targs=targs, args=args)
            case Compare(left=left, op=op, right=right):
                    return f"{emit_expr(left)} {op} {emit_expr(right)}"

            case Cond(expr=expr):
                bool_map = {
                    "or":"||",
                    "and":"&&"
                }
                match expr:
                    case UnaryOp(op="not", operand=operand):
                        return f"!{emit_expr(operand)}"
                    case BinOp(left=left, op=op ,right=right) if op in bool_map:
                        return f"{emit_expr(left)} {bool_map[op]}  {emit_expr(right)}"
                    case _:
                        return emit_expr(expr)
            case BinOp(left=left, op=op, right=right):
                op_map = {
                    "+":"+", "-":"-",
                    "*":"*", "/":"/", "%":"%"
                }
                return f"({self.emit_expr(left)} {op_map[op]}  {self.emit_expr(right)})"

            case UnaryOp(op="address_of", operand=operand):
                return f"&{self.emit_expr(operand)}"

            case UnaryOp(op="deref", operand=operand):
                return f"*{self.emit_expr(operand)}"

            case _:
                return super().emit_expr(node)
            
    def emit_const(self, v) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            return f'"{v}"'
        return str(v)

    def emit_attribute(self, node: Node) -> str:
        sep = '::'
        if node.kind == AttrKind.MEMBER:
            sep = '.'
        elif node.kind == AttrKind.POINTER:
            sep = "->"
        return self.emit_expr(node.value) + sep + node.attr

    def emit_template_call(self, func: Node, targs: list, args: list) -> str:
        args_s = ", ".join(self.emit_expr(a) for a in args)
        targs_s = ", ".join(_resolvetype(a, self.ctx) for a in targs)
        return f"{self.emit_expr(func)}<{targs_s}>({args_s})"
    def emit_array(self, node:Node ):
        if not node.elts:
            return "{}"
        elements = ", ".join(self.emit_expr(a) for a in node.elts)
        return "{"+ elements +"}"
    def emit_subscript(self, node):
        emit_expr = self.emit_expr # cache temporay to speed up 
        # because attribute look up is slower than LOAD_FAST
        return f"{emit_expr(node.value)}[{emit_expr(node.index)}]"
        

    # emit_pow, emit_floordiv, emit_binop, emit_call, etc: inherited from common
    # Uses unqualified pow() which is correct for C++ with <cmath>

def emit_expr(node: Node, *args,**kwargs) -> str:
    return CppExprGen(*args,**kwargs).emit_expr(node)
