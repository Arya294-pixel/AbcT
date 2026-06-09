# abct_ast/node.py
from __future__ import annotations
from dataclasses import dataclass
from types import FunctionType
from typing import List, Optional, Union, Tuple
from enum import Enum, auto
def frozendataclass(typeobj):
    return dataclass(
        slots=True, frozen=True,
        unsafe_hash=True
    )(typeobj)
# Base
class BaseEnum(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        """
        Overrides the default auto() value generation.
        Returns the member name formatted to Title Case.
        """
        return name.lower().capitalize()

class Node:
    def get_atributes(self):
        # 1. Gather all slot names across the entire inheritance chain
        attributes = set()
        for cls in self.__class__.__mro__:
            slots = getattr(cls, '__slots__', [])
            
            # Standardize single-string slots into a tuple
            if isinstance(slots, str):
                slots = (slots,)
                
            attributes.update(slots)
            
        # 2. Return a list of attributes, filtering out the method name
        return [attr for attr in attributes if not isinstance(attr, FunctionType) ]

    def __hash__(self):
        attr_tuple = ()
        for attribute in self.get_atributes():
            val = getattr(self, attribute)
            # CRITICAL: Handle lists by converting them to tuples for hashing
            if isinstance(val, list):
                # We turn the list into a tuple so it can be hashed
                attr_tuple += (hash(tuple(val)),)
            else:
                try:
                    attr_tuple += (hash(val),)
                except TypeError:
                    # Fallback for unhashable non-list types
                    attr_tuple += (0,)
        return hash(attr_tuple)


# Literals & Names
@frozendataclass
class Const(Node):
    value: Union[int, float, bool, str]

@frozendataclass
class Name(Node):
    id: str
    depth: int = 0 # 0:scalar 1: type[] 2: type[][] ...

# Expressions
@frozendataclass
class BinOp(Node):
    left: Node
    op: str
    right: Node

@frozendataclass
class Compare(Node):
    left: Node
    op: str
    right: Node

@frozendataclass
class UnaryOp(Node):
    op: str
    operand: Node

class AttrKind(BaseEnum):
    NAMESPACE = auto()     # std::cout
    STATIC = auto()        # ClassName::member
    MEMBER = auto()        # obj.field
    POINTER = auto()       # ptr->member

@frozendataclass
class Attribute(Node):
    value: Node
    attr: str
    kind: AttrKind = AttrKind.MEMBER


@frozendataclass
class Array(Node):
    depth: int # for cases like int[][] and int[]
    elts: list
    
class Ctx(BaseEnum):
    Load = auto()
    Store = auto()

@frozendataclass
class Subscript(Node):
    value: Node
    index: Node
    ctx: Ctx = Ctx.Load
    depth: int = 0 # cache var: value.depth - 1

@frozendataclass
class Call(Node):
    func: Node
    args: list
    keywords: list = None

@frozendataclass
class TemplateCall(Node):
    func: Node
    targs: list[str]
    args: list
    keywords: list = None

# Statements
@frozendataclass
class AnnAssign(Node):
    target: str
    annotation: str
    value: Optional[Node] = None

@frozendataclass
class Assign(Node):
    target: Node
    value: Node

@frozendataclass
class Expr(Node):
    value: Node

@frozendataclass
class Return(Node):
    value: Optional[Node] = None

@frozendataclass
class Cond(Node):
    # Can wrap a Compare, BinOp, Const, or UnaryOp node
    expr: Node  
    
    # Optional flags or metadata for optimization passes (e.g., compile-time static values)
    is_static: bool = False
    static_value: Optional[bool] = None


@frozendataclass
class If(Node):
    test: Cond
    body: list
    orelse: list = None

@frozendataclass
class While(Node):
    test: Cond
    body:list

@frozendataclass
class Pass(Node):
    pass

@frozendataclass
class Break(Node):
    level: int = 5

@frozendataclass
class Continue(Node):
    pass
@frozendataclass
class For(Node): # C-style: for(init; cond; update)
    header: tuple[Assign | AnnAssign | None, Node | None, Node | None]
    body: list

@frozendataclass
class Iter(Node):
    iterable: Node
    var: str
    body: list

@frozendataclass
class FuncDef(Node):
    name: Name
    ret: TypeRef | TemplateRef
    params: list[tuple[str, TemplateRef|TypeRef]]
    templates: list[TemplateDef]
    body: list

@frozendataclass
class Module(Node):
    stmts: list

@frozendataclass
class Import(Node):
    source: Name


# OOP
@frozendataclass
class ClassDef(Node):
    name: Name
    public_attributes: list[AnnAssign]
    private_attributes: list[AnnAssign]
    public_methods: list[FuncDef]
    private_methods: list[FuncDef]
    templates: list[TemplateDef]

class TemplateCapablity(BaseEnum):
    COMPARABLE = auto()
    DECIMAL = auto()
    INTEGER = auto()

    SUBSCRIPTABLE = auto()
    ITERABLE = auto()
    HASHABLE = auto()
    COPYABLE = auto()
    RUNTIME_CHECK = auto()
    NO_CHECK = auto()

    ANY = auto()
    UNKNOWN = auto()
    USER = auto()   # user protocols

# for definations of templates
@frozendataclass
class TemplateDef(Node):
    name: Name
    capablity: list[TemplateCapablity] = TemplateCapablity.ANY
    mangle:bool = False

#overide after dataclass completes it work
TemplateDef.__hash__ = Node.__hash__

# for accessing the templates
@frozendataclass
class TemplateRef(Node):
    name:Name
@frozendataclass
class TypeRef(Node):
    name:Name
