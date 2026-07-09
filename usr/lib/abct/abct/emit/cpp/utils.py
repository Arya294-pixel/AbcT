from pprint import pprint

from abct.abct_ast import *
from .types import ann_to_cpp

def _get_typedef_str(typedefs:list):
    if not typedefs: return ""
    string = ""
    for typedef, name in typedefs.items():
        pprint(f"[DEBUG]: {name=}, {typedef=}")
        string += f"\nusing {typedef} = {name};"
    return string + "\n"

def _get_mangled_template(template: TemplateDef):
    pprint(template)
    print(type(template))
    if not template.mangle:
        return template.name.id
    # 'template' is now a single object, not a list
    cap = "".join([c.name for c in sorted(template.capablity)])
    return f"{template.name.id}_M_{cap}"

def _get_mangled_template_ref(template:TemplateRef, ctx:dict):
    pprint(ctx)
    for t in ctx["templates"]:                                   
        if t.name.id == template.name.id:
            template = t
            pprint(t)
            break
    else:
            print("[DEBUG]: falling through fallback")
            pprint(template)
            return template.name.id
    return _get_mangled_template(template)

def _emit_template_header(templates: list[TemplateDef], ctx):
     if not isinstance(templates, list):
              templates = [templates]
     print("[DEBUG]: ",end='')
     pprint(templates)
     if not templates: return ""

     _templates = []
     typedefs = {}
     for template in templates:
        if template in ctx["emited_template"]:
            print(f"template {template} already emiited so not emitting")
            continue
        if not template.mangle:
             _templates.append(f"typename {template.name.id}")
        else:
             mangled_template = _get_mangled_template(template)
             typedefs[template.name.id] = mangled_template
             _templates.append(f"typename {mangled_template}")

     # Using a list and join ensures the order is preserved exactly as defined
     if not _templates: return ""
     main_str = f"template <{', '.join(_templates)}>\n"
     typedef_str = _get_typedef_str(typedefs)
     typedef_str = "" # clean using statements
     return main_str+typedef_str

def _resolvetype(obj: Type, ctx: dict, readonly=False):
    if isinstance(obj, ConstType):
        obj, readonly = obj.target, True
    def _resolve(obj: Type, ctx: dict):
        match obj:

            case TypeRef(name=name):
                return ann_to_cpp(name.id)

            case TemplateRef():
                return _get_mangled_template_ref(obj, ctx)

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
