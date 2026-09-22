from __future__ import annotations

from dataclasses import replace

from abct.abct_ast.node import *
from .expr import emit_expr
from .utils import _resolvetype


class EnumDispatcher:
    """
    Normalize an AbcT EnumDef into a form that the C++ emitter
    can directly emit.

    Semantic validation should happen before this stage.
    """

    def process(self, enum_node: EnumDef) -> EnumDef:
        # enum X { ... } -> enum X: int
        if enum_node.type is None:
            enum_type = TypeRef(
                name=Name(id="int")
            )
        else:
            enum_type = enum_node.type

        # Only automatically number integer enums.
        integer_types = {
            "i8", "i16", "i32", "i64",
            "u8", "u16", "u32", "u64",
            "int",
        }

        is_integer = (
            isinstance(enum_type, TypeRef)
            and enum_type.name.id in integer_types
        )

        members = []
        next_value = 0

        for member in enum_node.body:

            if member.value is None:
                if not is_integer:
                    # This should eventually be caught by
                    # semantic analysis, not here.
                    raise RuntimeError(
                        f"unresolved enum member: "
                        f"{enum_node.name.id}.{member.name.id}"
                    )

                value = Const(value=next_value)

            else:
                value = member.value

                # If it is a literal integer, we can continue
                # implicit numbering.
                if (
                    is_integer
                    and isinstance(value, Const)
                    and isinstance(value.value, int)
                ):
                    next_value = value.value + 1
                else:
                    # We cannot know the result yet.
                    next_value = None

            members.append(
                EnumAttr(
                    name=member.name,
                    value=value,
                )
            )

            if (
                is_integer
                and member.value is None
            ):
                next_value += 1

        return EnumDef(
            name=enum_node.name,
            type=enum_type,
            body=members,
        )

class EnumEmitter:

    def __init__(self, main_emitter=None):
        self.main_emit = main_emitter

    def emit(self, node: EnumDef, ctx: dict) -> str:
        node = EnumDispatcher().process(node)

        enum_name = node.name.id
        enum_type = _resolvetype(node.type, ctx)

        out = f"struct {enum_name} {{\n"

        # Underlying type
        out += f"    using type = {enum_type};\n"

        # Stored value
        out += "    type value;\n\n"

        # Constructor
        out += (
            f"    constexpr {enum_name}(type value)"
            f" : value(value) {{}}\n\n"
        )

        # Conversion to underlying type
        out += (
            "    constexpr operator type() const {\n"
            "        return value;\n"
            "    }\n\n"
        )

        # Enum members
        for member in node.body:
            out += (
                f"    static const {enum_name} "
                f"{member.name.id};\n"
            )

        out += "};\n\n"

        # Member definitions
        for member in node.body:
            if member.value is None:
                # Semantic analysis should have resolved this
                # before reaching the emitter.
                raise RuntimeError(
                    f"unresolved enum member: "
                    f"{enum_name}.{member.name.id}"
                )

            value = emit_expr(member.value, ctx)

            out += (
                f"constexpr {enum_name} "
                f"{enum_name}::{member.name.id}"
                f"{{{value}}};\n"
            )

        return out.rstrip()
