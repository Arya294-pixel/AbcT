from ..abct_ast import (
    Module,
    EnumDef,
    TypeRef,
    Name,
)


INTEGER_TYPES = {
    "i8",
    "i16",
    "i32",
    "i64",
    "u8",
    "u16",
    "u32",
    "u64",
    "int",
    "uint",
    "short",
    "ushort",
    "long",
    "ulong",
}


def _type_name(type_):
    if isinstance(type_, TypeRef):
        return type_.name.id

    return None


def _is_integer_type(type_):
    return _type_name(type_) in INTEGER_TYPES


def _deduce_type(node):
    if node.type is not None:
        return node.type

    return TypeRef(
        name=Name(id="int")
    )


def _verify_enum(node: EnumDef):
    enum_type = _deduce_type(node)
    integer_enum = _is_integer_type(enum_type)

    names = set()

    for member in node.body:
        name = member.name.id

        if name in names:
            raise ValueError(
                f"duplicate enum member "
                f"'{node.name.id}.{name}'"
            )

        names.add(name)

        if member.value is None and not integer_enum:
            raise ValueError(
                f"enum '{node.name.id}' member "
                f"'{name}' requires an explicit value"
            )


def verify(ast: Module):
    """
    Verify all enums in a module.
    """

    for node in ast.body:
        if isinstance(node, EnumDef):
            _verify_enum(node)
