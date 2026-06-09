# abct/emit/cpp/types.py
from __future__ import annotations

TYPE_MAP = {
    "i8": "std::int8_t",
    "i16": "std::int16_t",
    "i32": "std::int32_t",
    "i64": "std::int64_t",
    "u8": "std::uint8_t",
    "u16": "std::uint16_t",
    "u32": "std::uint32_t",
    "u64": "std::uint64_t",
    "f32": "float",
    "f64": "double",
    "int": "int",
    "float": "double",
    "bool": "bool",
    "str": "std::string",
    "string":"std::string",
    "void": "void",
    "None": "void",
    "auto": "auto"
}

def ann_to_cpp(ann: str) -> str:
    if not isinstance(ann, str):
        # Fallback if builder still returns a Tree somehow
        return "auto"

    depth = ann.count("[]")
    ptr_depth = ann.count("*")
    base = ann.replace("[]", "")
    base = base.replace("*", "")

    cpp_base = TYPE_MAP.get(base, base)

    for _ in range(depth):
        cpp_base = f"std::vector<{cpp_base}>"
    cpp_base += "*" * ptr_depth

    return cpp_base
