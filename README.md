# AbcT

**AbcT** is a programming language and transpiler that translates AbcT source code into C++.

## Overview

AbcT follows a C++-based compilation model.

```text
                         AbcT source
                              |
                              v
                           abcTCpp
                              |
              +---------------+---------------+
              |                               |
              v                               v
           C++ source                      C++ header
            (.cpp)                           (.hpp)
              |
              v
          clang++ / g++
              |
       +------+------+------+
       |      |      |
       v      v      v
     .out    .ll    .s
```

The main compilation pipeline is:

```text
.ab
 |
 v
Lexer
 |
 v
Parser
 |
 v
AST
 |
 v
Semantic analysis
 |
 v
C++ emitter
 |
 v
.cpp / .hpp
 |
 v
clang++ / g++
 |
 v
Executable / compiler output
```

`abcTCpp` is the AbcT-to-C++ transpilation stage, while `abct` acts as the main compiler driver.

## Commands

### `abct`

The main AbcT compiler driver.

```bash
abct program.ab -o program.out
```

The normal pipeline is:

1. Read the `.ab` source file.
2. Transpile it to C++ through `abcTCpp`.
3. Compile the generated C++ using `clang++` or `g++`.
4. Produce the requested output.

Example:

```bash
abct hello.ab -o hello
./hello
```

`clang++` is preferred when available, with `g++` used as a fallback.

Additional compiler arguments can be passed to the C++ compiler:

```bash
abct program.ab -o program --extra-compile-args="..."
```

Compiler output modes such as assembly or LLVM IR can also be requested through compiler arguments.

### `abcTCpp`

Runs the AbcT-to-C++ transpilation stage directly.

```bash
abcTCpp program.ab -o program.cpp
```

This is useful when you want to inspect the generated C++ before compiling it.

Module generation is also supported:

```bash
abcTCpp program.ab -m MyModule -o MyModule.hpp
```

## Language

### Functions

Functions use the `fn` keyword.

```text
fn add(a: int, b: int) -> int {
    return a + b;
}
```

### Variables

Typed declarations are supported:

```text
x: int = 10;
name: str = "AbcT";
```

Assignments are also supported:

```text
x = 20;
```

### Classes

Classes can contain public and private members.

```text
class Foo {
public:
    value: int = 10;

    fn get_value() -> int {
        return value;
    }
}
```

If a class does not explicitly specify a base class, the current implementation uses `Object` as its default base.

### Visibility

Public and private class members are supported.

```text
class Example {
public:
    value: int;

    fn get_value() -> int {
        return value;
    }

private:
    secret: int;
}
```
you may use NoInherit to avoid ant kind of inhertance

### Constructors

Constructors use the `__construct__` dunder function.

```text
class Foo {
    fn __construct__(value: int) -> NoReturnType {
        ...
    }
}
```

Objects are instantiated using the class name:

```text
foo = Foo();
```

The C++ emitter converts `__construct__` into the corresponding C++ constructor.

### Destructors

The `__destruct__` dunder is mapped to a C++ destructor.

```text
fn __destruct__() -> NoReturnType {
    ...
}
```

### String representation

Classes can define `__str__`.

When declared `readonly`, the method is emitted as a C++ `const` member function.

```text
fn readonly __str__() -> str {
    return "Foo";
}
```

The runtime also provides a default `Object` string representation.

### Templates

Template declarations and template types are supported.

```text
template <typename T, typename U>

class Pair {
public:
    first: T;
    second: U;
}
```

Template calls are also supported by the parser and C++ emitter.

### Control flow

Supported control-flow constructs include:

- `if`
- `elif`
- `else`
- `switch`
- `match`
- `case`
- `while`
- `do`
- `iter`

Example:

```text
if x > 10 {
    print("large");
} else {
    print("small");
}
```

Range-based iteration is emitted as a C++ range-based `for` loop.

```text
iter item in items {
    print(item);
}
```

### Loop control

The following statements are supported:

```text
break;
continue;
pass;
```

### Exceptions

Exception-related constructs include:

```text
try {
    ...
}
catch {
    ...
}
```

and:

```text
throw value;
```

These are emitted to their corresponding C++ exception constructs.

## Types

The C++ backend currently maps several AbcT types to C++ types.

| AbcT | C++ |
|---|---|
| `i8` | `std::int8_t` |
| `i16` | `std::int16_t` |
| `i32` | `std::int32_t` |
| `i64` | `std::int64_t` |
| `u8` | `std::uint8_t` |
| `u16` | `std::uint16_t` |
| `u32` | `std::uint32_t` |
| `u64` | `std::uint64_t` |
| `f32` | `float` |
| `f64` | `double` |
| `int` | `int` |
| `float` | `double` |
| `bool` | `bool` |
| `str` | `std::string` |
| `string` | `std::string` |
| `void` | `void` |
| `None` | `void` |
| `auto` | `auto` |
| `NoReturnType` | constructor-style/no return type |

Pointers, references, rvalue references, arrays, `readonly`, and template types are represented by the parser and C++ emitter.

## Semantic Analysis

AbcT currently includes an experimental semantic-analysis stage.

The current analyser performs basic declaration and scope checks, including:

- Duplicate variable declarations
- Duplicate parameters
- Duplicate function signatures
- Duplicate class declarations
- Basic scope tracking
- Restrictions on certain declarations inside functions

Semantic analysis is **not yet a complete static type-checking system**.

## Runtime

Generated C++ code includes the AbcT runtime.

The runtime headers are installed under:

```text
/usr/include/abct/
```

Important runtime components include:

```text
AbcTRuntime.hpp
AbcTBuiltIn.hpp
AbcTTypes.hpp
AbcTIO.hpp
AbcTFS.hpp
AbcTStringUtils.h
```

The default `Object` implementation provides a string representation similar to:

```text
<Object at 0x...>
```

## Samples

The project includes sample AbcT programs and their generated C++ files.

They are located under:

```text
/usr/lib/abct/abct/sample/
```

Current samples include:

- Classes
- Control flow
- Matrix filtering
- Templates

## Architecture

The current project is organized around the compiler, parser, AST, emitter, semantic-analysis, runtime, and sample components.

```text
usr/
├── bin/
│   ├── abct
│   ├── abcTCpp
│   └── ...
│
├── include/
│   └── abct/
│       ├── AbcTBuiltIn.hpp
│       ├── AbcTFS.hpp
│       ├── AbcTIO.hpp
│       ├── AbcTRuntime.hpp
│       ├── AbcTStringUtils.h
│       ├── AbcTTypes.h
│       └── AbcTTypes.hpp
│
└── lib/
    └── abct/
        └── abct/
            ├── abct_ast/
            ├── compiler/
            ├── emit/
            ├── modules/
            ├── parser/
            ├── sample/
            ├── semamtics/
            └── utils/
```

## Development Status

AbcT is currently under active development.

Implemented areas include:

- Lexer
- Parser
- AST generation
- C++ code generation
- Classes
- Public/private members
- Constructors and destructors
- `__str__`
- Templates
- Pointers and references
- Control flow
- Exceptions
- Basic semantic analysis
- Runtime headers
- Direct C++ transpilation through `abcTCpp`

Some parts of the compiler are still experimental and subject to change.

## Roadmap

Future development may include improvements to:

- Semantic analysis
- Type checking
- Compiler diagnostics
- Error reporting
- Testing
- Tooling
- Standard-library/runtime support
- Language consistency
- Build and release infrastructure

Features listed here should not be considered implemented unless they are present in the current compiler.

## Contributing

Contributions, bug reports, experiments, and improvements are welcome.

Before contributing, inspect the existing compiler architecture and samples to understand how AbcT syntax is represented in the AST and emitted as C++.

## License

AbcT is released under the MIT License.
