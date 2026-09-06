# AbcT

**AbcT** is a programming language and transpiler that translates AbcT source code into C++.

The project provides two main command-line tools:

- `abct` — the main compiler driver. It transpiles AbcT to C++ and then uses `clang++` or `g++` to produce the requested output.
- `abcTCpp` — the direct AbcT-to-C++ transpiler.

AbcT is currently under active development.

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
