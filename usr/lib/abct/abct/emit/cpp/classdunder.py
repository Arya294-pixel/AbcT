# abct/emit/cpp/classdunder.py
from __future__ import annotations

from dataclasses import field, replace
from pprint import pprint

from abct.abct_ast import node as base_node
from .utils import _emit_template_header, _resolvetype

@base_node.frozendataclass
class DunderFuncDef(base_node.FuncDef):
    initializer_list: list = field(default_factory=list)

class DunderDispatcher:
    def process(self, class_node):
        # 1. Check for Iterability
        has_iter = any(m.name.id == "__iterate__" for m in class_node.public_methods)
        if has_iter and "Iterable" not in class_node.templates: # Simplified logic
            # Add "Iterable" trait to the class metadata
            pass 
        new_methods = list(class_node.public_methods)
        public_methods = class_node.public_methods

        # 2. Normalize Constructors/Destructors
        for i, method in enumerate(new_methods):
            if method.name.id in ["__construct__", "__destruct__"]:
                # Upgrade to DunderFuncDef
                new_method = DunderFuncDef(
                    name=method.name,
                    params=method.params,
                    ret=method.ret,
                    body=method.body,
                    templates=method.templates,
                    initializer_list=self._parse_inits(method.body)
                )
                
                # Rename for C++
                if new_method.name.id == "__construct__":
                    target_name = class_node.name.id
                else:
                    target_name = f"~{class_node.name.id}"
                new_name = replace(method.name, id=target_name)
                new_method = replace(new_method, name=new_name)
                public_methods[i] = new_method
        class_node = replace(class_node, public_methods=public_methods)
        return class_node

    def _parse_inits(self, body):
        # Logic to extract 'data = input' into initializer_list
        return [] 

# abct/emit/cpp/classdunder.py

class DunderEmitter:
    def __init__(self, main_emitter):
        self.main_emit = main_emitter  # The 'main' emit_stmt function

    def emit_construct(self, node, class_name, ctx):
        # Delegate block emission to the main system
        body_code = self.emit(node.body, ctx)
        
        # Build the initializer string
        inits = ", ".join([f"{attr}({self.emit(val, ctx)})" for attr, val in node.initializer_list])
        init_str = f" : {inits}" if inits else ""

        params = [f"{_resolvetype(ptype, ctx)} {pname}" for pname, ptype in node.params]
        params_str = "".join(params)
        return f"{class_name}({params_str}) {init_str} {{\n {body_code} }}"

    def emit_destruct(self, node, class_name, ctx):
        # Simply delegate the body generation
        body_code = self.emit(node.body, ctx)
        return f"~{class_name}() {{ {body_code} }}"
    
    def emit_class(self, node: Node, ctx: Dict):
        # Trigger the normalization
        node = DunderDispatcher().process(node)
        templates = node.templates
        ctx["templates"] += templates
        ctx["current_class_name"] = node.name.id
        header = _emit_template_header(templates, ctx)
        ctx["emited_template"].extend(templates)
        # Header and Start
        out = f"{header}"
        out += f"class {node.name.id} {{\n"
        
        # Public section
        if node.public_methods or node.public_attributes:
            out += "public:\n"
            pprint(node.public_attributes + node.public_methods)            
            out += self.emit_block(node.public_attributes + node.public_methods, ctx, sep="\n")

        for m in node.private_methods or node.private_attributes:
            out += "private:\n"
            out += self.emit_block(node.private_attributes + node.private_methods, ctx, sep="\n")
        
        return out + "};"
    def emit_block(self, nodelist:list[Node], ctx, sep):
        out = sep
        for node in nodelist:
            print("[DEBUG]: {emit_block} (as_ast)", node)
            out += self.emit(node, ctx) + sep
            print("[DEBUG]: {emit_block} (as_str):", repr(out))
        return out
    def emit(self, node, ctx):
        if isinstance(node, list):
            self.emit_block(node, ctx, sep="\n")
        print("[DEBUG] {emit}:", node)
        # Use match-case to delegate based on node type
        match node:
            case DunderFuncDef():
                # We need to distinguish between constructor and destructor here
                # A simple check on the name prefix '~' works well
                if node.name.id.startswith("~"):
                    return self.emit_destruct(node, ctx["current_class_name"], ctx)
                return self.emit_construct(node, ctx["current_class_name"], ctx)

            case _:
                return self.main_emit(node, ctx)
