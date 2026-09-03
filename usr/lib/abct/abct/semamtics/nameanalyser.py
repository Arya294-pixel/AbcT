from __future__ import annotations

from dataclasses import dataclass, field

from ..abct_ast.node import (
    Module,
    FuncDef,
    ClassDef,
    AnnAssign,
    Name,
)


@dataclass
class Scope:
    parent: Scope | None = None
    kind: str = "module"

    variables: set[str] = field(default_factory=set)
    functions: set[tuple] = field(default_factory=set)
    classes: set[str] = field(default_factory=set)


class SemanticAnalyser:
    def __init__(self):
        self.scope = Scope(kind="module")

    # ---------------------------------------------------------
    # Scope
    # ---------------------------------------------------------

    def push_scope(self, kind: str) -> None:
        self.scope = Scope(
            parent=self.scope,
            kind=kind,
        )

    def pop_scope(self) -> None:
        if self.scope.parent is not None:
            self.scope = self.scope.parent

    # ---------------------------------------------------------
    # Entry point
    # ---------------------------------------------------------

    def analyse(self, ast: Module) -> None:
        self.visit_module(ast)

    # ---------------------------------------------------------
    # Module
    # ---------------------------------------------------------

    def visit_module(self, node: Module) -> None:
        for stmt in node.stmts:
            self.visit(stmt)

    # ---------------------------------------------------------
    # Dispatcher
    # ---------------------------------------------------------

    def visit(self, node) -> None:
        if isinstance(node, FuncDef):
            self.visit_funcdef(node)

        elif isinstance(node, ClassDef):
            self.visit_classdef(node)

        elif isinstance(node, AnnAssign):
            self.visit_annassign(node)

        elif isinstance(node, Module):
            self.visit_module(node)

        else:
            self.visit_children(node)

    # ---------------------------------------------------------
    # Variables
    # ---------------------------------------------------------

    def visit_annassign(self, node: AnnAssign) -> None:
        name = node.target.id

        if name in self.scope.variables:
            raise Exception(
                f"duplicate variable declaration: {name}"
            )

        self.scope.variables.add(name)

        # The initializer is still analysed.
        if node.value is not None:
            self.visit(node.value)

    # ---------------------------------------------------------
    # Functions
    # ---------------------------------------------------------

    def function_signature(self, node: FuncDef) -> tuple:
        name = node.name.id

        parameter_types = tuple(
            self.type_key(param_type)
            for _, param_type in node.params
        )

        return (
            name,
            parameter_types,
        )

    def visit_funcdef(self, node: FuncDef) -> None:
        # Functions cannot be declared inside functions.
        if self.scope.kind == "function":
            raise Exception(
                f"function declaration inside function: "
                f"{node.name.id}"
            )

        signature = self.function_signature(node)

        if signature in self.scope.functions:
            raise Exception(
                f"duplicate function declaration: "
                f"{node.name.id}"
            )

        self.scope.functions.add(signature)

        # Function body gets its own scope for variables.
        self.push_scope("function")

        # Parameters are declarations in the function scope.
        for name, _ in node.params:
            if name in self.scope.variables:
                raise Exception(
                    f"duplicate parameter declaration: {name}"
                )

            self.scope.variables.add(name)

        for stmt in node.body:
            self.visit(stmt)

        self.pop_scope()

    # ---------------------------------------------------------
    # Classes
    # ---------------------------------------------------------

    def visit_classdef(self, node: ClassDef) -> None:
        name = node.name.id

        if self.scope.kind == "function":
            raise Exception(
                f"class declaration inside function: {name}"
            )

        if name in self.scope.classes:
            raise Exception(
                f"duplicate class declaration: {name}"
            )

        self.scope.classes.add(name)

        self.push_scope("class")

        # Both lists belong to the SAME class namespace.
        for attr in node.public_attributes:
            self.visit(attr)

        for attr in node.private_attributes:
            self.visit(attr)

        for method in node.public_methods:
            self.visit(method)

        for method in node.private_methods:
            self.visit(method)

        self.pop_scope()

    # ---------------------------------------------------------
    # Type representation
    # ---------------------------------------------------------

    def type_key(self, type_node):
        """
        Produce a hashable representation of a type.

        This is intentionally small for the first analyser.
        It can later be replaced by proper type canonicalisation.
        """
        if type_node is None:
            return None

        cls = type(type_node).__name__

        if hasattr(type_node, "name"):
            name = type_node.name

            if isinstance(name, Name):
                return (
                    cls,
                    name.id,
                    name.depth,
                )

            return (cls, str(name))

        if hasattr(type_node, "target"):
            return (
                cls,
                self.type_key(type_node.target),
            )

        if hasattr(type_node, "args"):
            return (
                cls,
                self.type_key(type_node.target),
                tuple(
                    self.type_key(arg)
                    for arg in type_node.args
                ),
            )

        return (cls, repr(type_node))

    # ---------------------------------------------------------
    # Generic traversal
    # ---------------------------------------------------------

    def visit_children(self, node) -> None:
        """
        Generic traversal for AST nodes that don't introduce
        declarations/scopes.

        Dataclasses are used throughout the AST, so fields can
        be traversed recursively.
        """
        from dataclasses import fields, is_dataclass

        if not is_dataclass(node):
            return

        for field_info in fields(node):
            value = getattr(node, field_info.name)

            if isinstance(value, list):
                for item in value:
                    if hasattr(item, "__class__"):
                        self.visit(item)

            elif isinstance(value, tuple):
                for item in value:
                    if hasattr(item, "__class__"):
                        self.visit(item)

            elif value is not None:
                self.visit(value)

    def verify(self, ast: Module) -> None:
            self.visit_module(ast)
