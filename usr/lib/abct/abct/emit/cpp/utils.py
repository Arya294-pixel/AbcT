from pprint import pprint

from abct.abct_ast import *
from .types import ann_to_cpp

def _emit_template_header(templates: list[TemplateDef], ctx):
    if not isinstance(templates, list):
        templates = [templates]

    if not templates:
        return ""

    _templates = []

    for template in templates:
        if template in ctx["emited_template"]:
            continue

        _templates.append(f"typename {template.name.id}")

    if not _templates:
        return ""

    return f"template <{', '.join(_templates)}>\n"

def _resolvetype(obj: Type, ctx: dict, readonly=False):
    if isinstance(obj, ConstType):
        obj, readonly = obj.target, True
    def _resolve(obj: Type, ctx: dict):
        match obj:

            case TypeRef(name=name):
                return ann_to_cpp(name.id)

            case TemplateRef(name=name):
                return name.id

            case PtrType(target=target):
                return _resolve(target, ctx) + "*"

            case RefType(target=target):
                return _resolve(target, ctx) + "&"

            case RValueRefType(target=target):
                return _resolve(target, ctx) + "&&"

            case ArrayType(target=target):
                return f"std::vector<{_resolvetype(target, ctx)}>"

            case TemplateType(target=target, args=args):

                base = _resolve(target, ctx)

                arg_str = ", ".join(
                    _resolve(arg, ctx) for arg in args
                )

                return f"{base}<{arg_str}>"

            case str():
                return ann_to_cpp(obj)

            case _:
                raise TypeError(
                    f"unknown type node {type(obj).__name__}: {obj!r}",
                )
    if not readonly:
        return _resolve(obj, ctx)
    val = _resolve(obj, ctx)
    if "const" in  val.split():
        return val
    if not val:
        return ""
    return f"const {val.strip()}"
