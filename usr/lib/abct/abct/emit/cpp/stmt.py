# abct/emit/cpp/stmt.py
from __future__ import annotations
from abct.abct_ast.node import *
from .expr import emit_expr
from .types import ann_to_cpp
from .include import *
from pprint import pprint  #for debugging

def _get_typedef_str(typedefs:list):
    if not typedefs: return ""
    string = ""
    for typedef, name in typedefs.items():
        pprint(f"[DEBUG]: {name=}, {typedef=}")
        string += f"\nusing {typedef} = {name};"
    return string + "\n"

def _get_mangled_template(template: TemplateDef):
    # 'template' is now a single object, not a list
    cap = "".join([c.name for c in sorted(template.capablity)])
    return f"{template.name.id}_M_{cap}"

def _get_mangled_template_ref(template:TemplateRef, ctx:dict):
    for t in ctx["templates"]:
        if t.name.id == template.name.id:
            template = t
            break
    else:
        print("[DEBUG]: falling thorogh fallback")
        pprint(template) 
        pprint(ctx)
        return template.name.id
    cap = "".join([c.name for c in sorted(template.capablity)])
    return f"{template.name.id}_M_{cap}"

def _emit_template_header(templates: list[TemplateDef]):
    if not isinstance(templates, list):
        templates = [templates]
    print("[DEBUG]: ",end='')
    pprint(templates)
    if not templates: return ""
    
    _templates = []
    typedefs = {}
    for template in templates:
        if template.mangle:
            _templates.append(f"typename {template.name.id}")
        else:
            mangled_template = _get_mangled_template(template)
            typedefs[template.name.id] = mangled_template
            _templates.append(f"typename {mangled_template}")
        
    # Using a list and join ensures the order is preserved exactly as defined
    main_str = f"template <{', '.join(_templates)}>\n"
    typedef_str = _get_typedef_str(typedefs)
    return main_str+typedef_str
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
    # FIX 2: Completely removed 'global local_modules' and the top-level declaration
    match node:
        case Import(source=source):
            ctx["local_modules"].add(f'#include "{source.id}.hpp"')
            return "" # FIX 3: Explicitly return empty string to prevent implicit NoneType bugs

        case AnnAssign(target=t, annotation=ann, value=val):
            cpp_type = ann_to_cpp(ann)
            return f"{cpp_type} {t};" if val is None else f"{cpp_type} {t} = {emit_expr(val)};"

        case Assign(target=t, value=val):
            return f"{emit_expr(t)} = {emit_expr(val)};"
            
        case FuncDef(name=name, params=params, ret=ret, body=body, templates=templates):
            # 1. Update context scope for mangling/resolution
            old_templates = ctx.get("templates", [])
            ctx["templates"] = templates
            
            header = _emit_template_header(templates)
            
            # 2. Resolve Return Type
            if isinstance(ret, TemplateRef):
                ret_type = _get_mangled_template_ref(ret)
            else:
                ret_type = ann_to_cpp(ret.name.id)

            # 3. Resolve Parameters
            cpp_args = []
            for pname, ptype_node in params:
                if isinstance(ptype_node, TemplateRef):
                    # For templates, use the identifier directly
                    p_type_str = _get_mangled_template_ref(ptype_node,ctx)
                else:
                    # For concrete types, use your type mapper
                    p_type_str = ann_to_cpp(ptype_node)
                
                cpp_args.append(f"{p_type_str} {pname}")

            # 4. Construct Output
            out = f"{header}{ret_type} {name.id}({', '.join(cpp_args)}) {{\n"
            out += _emit_block(body, ctx)
            out += "}"
            
            # 5. Restore previous context scope
            ctx["templates"] = old_templates
            return out

        case ClassDef(name=name, public_attributes=pub_attrs, 
                      private_attributes=priv_attrs, public_methods=pub_methods, 
                      private_methods=priv_methods, templates=templates):
            
            header = _emit_template_header(templates)
            out = f"{header}class {name.id} {{\n"
            
            # Combine logic as discussed
            if pub_attrs or pub_methods:
                out += "public:\n"
                out += _emit_block(pub_attrs + pub_methods, ctx)
            
            if priv_attrs or priv_methods:
                out += "private:\n"
                out += _emit_block(priv_attrs + priv_methods, ctx)

            out += "};"
            return out

        case Expr(value=val):
            return f"{emit_expr(val)};"

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
        "templates": [],
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
        print(f"[DEBUG]: {s = }")
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

    out = "// Generated by Timber\n"
    out += "// this file should not be touched by user directly\n"
    if includes:
        out += includes + "\n\n"

    if local_includes:
        out += local_includes + "\n\n"

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
