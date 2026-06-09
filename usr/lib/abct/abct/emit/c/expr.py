# abct/emit/c/expr.py
from abct.emit.common.expr import CAndCppCommonExpr
from abct_ast.node import *

class CExprGen(CAndCppCommonExpr):
    def emit_const(self, v) -> str:
        if isinstance(v, bool): return "1" if v else "0"
        if isinstance(v, str): return f'"{v}"'
        return str(v)

    def emit_attribute(self, value: Node, attr: str) -> str:
        raise NotImplementedError("C has no namespace :: operator")

    def emit_template_call(self, func, targs, args):
        raise NotImplementedError("C does not support templates")

    # Uses common emit_pow: "pow(l, r)" - correct for C

def emit_expr(node):
    return CExprGen().emit_expr(node)
