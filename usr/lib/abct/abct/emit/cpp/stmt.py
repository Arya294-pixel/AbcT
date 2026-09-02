# abct/emit/cpp/stmt.py
from __future__ import annotations
from abct.abct_ast.node import *
from .expr import emit_expr
from .types import ann_to_cpp
from .include import *
from .utils import  _resolvetype, _emit_template_header
from .classdunder import *

from pprint import pprint  #for debugging

def _emit_block(stmts, ctx: dict) -> str:
    """Handle both list and single node, with indentation"""
    if stmts is None:
        return ""
    if not isinstance(stmts, list):
        stmts = [stmts]

    out = ""
    for s in stmts:
        stmt_str = emit_stmt(s, ctx) 
        for line in stmt_str.split("\n"):
            if line.strip():
                out += f" {line}\n"
    return out

def emit_cond(node: Node) -> str:
    """Emits conditional logic, handling compulsory boolean transformations"""
    match node:
        case Cond(expr=inner_expr):
            return emit_cond(inner_expr)

        case UnaryOp(op="not", operand=operand):
            return f"!({emit_cond(operand)})"

        case BinOp(left=left, op="and", right=right):
            return f"({emit_cond(left)}) && ({emit_cond(right)})"

        case BinOp(left=left, op="or", right=right):
            return f"({emit_cond(left)}) || ({emit_cond(right)})"

        # If it's a standard expression (Compare, Name, Const), fall back to emit_expr
        case _:
            return emit_expr(node)


def emit_stmt(node: Node, ctx: dict[str, object]) -> str:
    if isinstance(node, list):
        return _emit_block(node, ctx)
    # FIX 2: Completely removed 'global local_modules' and the top-level declaration
    match node:
        case Import(source=source):
            ctx["local_modules"].add(f'#include "{source}"')
            return "" # FIX 3: Explicitly return empty string to prevent implicit NoneType bugs
        case Include(source=source):
            ctx["system_modules"].add(f"#include <{source}>")
            return ""

        case AnnAssign(target=target, annotation=ann, value=val):
            cpp_type = _resolvetype(ann, ctx)

            if isinstance(target, Name): target = target.id

            return f"{cpp_type} {target};" if val is None else f"{cpp_type} {target} = {emit_expr(val, ctx)};"

        case Assign(target=t, value=val):
            return f"{emit_expr(t, ctx)} = {emit_expr(val, ctx)};"
            
        case FuncDef(name=name, params=params, ret=ret, body=body, templates=templates, readonly=readonly):
            # 1. Update context scope for mangling/resolution
            old_templates = ctx.get("templates", [])
            ctx["templates"] = templates + old_templates
            in_class_scope = "" != ctx["current_class_name"]

            header = _emit_template_header(templates, ctx)
            
            # 2. Resolve Return Type
            ret_type = _resolvetype(ret, ctx)
            # 3. Resolve Parameters
            cpp_args = []
            parameter_readonly = readonly and not in_class_scope
            for pname, ptype_node in params:
                p_type_str = _resolvetype(ptype_node, ctx,readonly=parameter_readonly)
                
                cpp_args.append(f"{p_type_str} {pname}")

            readonly_member = in_class_scope and readonly

            # 4. Construct Output
            if ret_type == "": # constructor/NoReturnType case
                out = f"{header} {name.id}({', '.join(cpp_args)}) {{\n"
            else:
                if readonly_member:
                    out = f"{header}{ret_type} {name.id}({', '.join(cpp_args)}) const {{\n"
                else: 
                    out = f"{header}{ret_type} {name.id}({', '.join(cpp_args)}) {{\n"
            out = out.strip()
            out += _emit_block(body, ctx)
            out += "}"

            # 5. Restore previous context scope
            ctx["templates"] = old_templates
            return out

        case TryCatch(try_body=try_body, catch_blocks=catch_blocks):
            out = "try {\n"
            out += _emit_block(try_body, ctx)
            out += "}"

            for catch_block in catch_blocks:
                exception_type = catch_block.exception_type
                exception_name = catch_block.exception_name
                body = catch_block.body

                if exception_type is None:
                    out += " catch (...) {\n"
                else:
                    cpp_type = _resolvetype(exception_type, ctx)
                    if exception_name is None:
                        out += f" catch ({cpp_type}) {{\n"
                    else:
                        out += f" catch ({cpp_type} {exception_name.id}) {{\n"

                out += _emit_block(body, ctx)
                out += "}"

            return out

        case Throw(Expr(value=value)):
            return f"throw {emit_expr(value, ctx)};"

        case Expr(value=val):
            return f"{emit_expr(val, ctx)};"

        case Return(value=val):
            return "return;" if val is None else f"return {emit_expr(val)};"

        case If(test=test, body=body, orelse=orelse):
            out = f"if ({emit_cond(test)}) {{\n"
            out += _emit_block(body, ctx) # FIX 1: Forward ctx down
            out += "}"
            if orelse:
                out += " else {\n"
                out += _emit_block(orelse, ctx) # FIX 1: Forward ctx down
                out += "}"
            return out

        case While(test=test, body=body):
            out = f"while ({emit_expr(test)}) {{\n"
            out += _emit_block(body, ctx) # FIX 1: Forward ctx down
            out += "}"
            return out

        case For(target=target, iterable=iter_, body=body):
            out = f"for (auto {target} : {emit_expr(iter_)}) {{\n"
            out += _emit_block(body, ctx) # FIX 1: Forward ctx down
            out += "}"
            return out

        case Iter(iterable=iter_, var=var, body=body):
            out = f"for (auto {var} : {emit_expr(iter_)}) {{\n"
            out += _emit_block(body, ctx) # FIX 1: Forward ctx down
            out += "}"
            return out

        case ClassDef():
            return DunderEmitter(main_emitter=emit_stmt).emit_class(node, ctx)
        case TemplateDef():
            return _emit_template_header(node, ctx)

        case Break(level=level):
            return "break;" # level ignored in C++

        case Continue():
            return "continue;"

        case Pass():
            return ";"

        case _:
            raise NotImplementedError(f"emit_stmt not implemented for {type(node).__name__}")


# for now but in future this wil be modified by other codes like compiler.py
start_headers = "#pragma once\n"
end_headers = ""

def emit_module(module: Module, as_module=False, module_name="module") -> str:
    ctx = {
        "local_modules": set(),
        "system_modules": set(),
        "templates": [],
        "emited_template": [],
        "current_class_name":''
    }
    if not module.stmts:
        out  = "// Generated by Timber\n"
        if as_module:
            return start_headers + out + end_headers
        out += "int main() {\n"
        out += "return 0;\n"
        out += "}"
        return out

    collector = IncludeCollector()
    for s in module.stmts:
        pprint(f"[DEBUG]: {s = }")
        collector.visit(s)

    arr = []
    for s in module.stmts:
        string = emit_stmt(s, ctx)
        if string.strip(): # Avoid pushing empty string newlines from Import nodes into arr
            arr.append(string)

    # FIX 4: Moved out of the loop body block to stop re-running it continuously
    body = "\n\n".join(arr)

    includes = "\n".join(collector.render())
    # FIX 5: Use sorted() to keep the include output deterministic and pristine
    local_includes = "\n".join(sorted(ctx["local_modules"])) 
    system_includes = "\n".join(sorted(ctx["system_modules"])) 

    out = "// Generated by Timber\n"
    out += "// this file should not be touched by user directly\n"
    if includes:
        out += includes + "\n\n"

    if local_includes:
        out += local_includes + "\n\n"
    if system_includes:
        out += system_includes + "\n\n"

    namespace_code = ""
    if as_module:
        # Fix trailing whitespace generation bug on blank lines inside the namespace block
        namespace_body = "\n".join([" "*4+a if a.strip() else "" for a in body.splitlines()])
        namespace_body = f"namespace {module_name} " + "{\n\n" + namespace_body
        namespace_body += f"\n}} // namespace {module_name}"
        namespace_code =  namespace_body

    out += body
    if not as_module:
        return out
    return "\n\n".join([start_headers, out, namespace_code, end_headers])
