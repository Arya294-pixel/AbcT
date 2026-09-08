#!/usr/bin/env python3
import argparse
import sys
import os

from abct.parser.builder import Parser
from abct.emit.cpp.stmt import emit_module
from abct.semamtics import verify

invalid_namespace = "$namespace$"

def main(argv=None):
    parser = argparse.ArgumentParser("AbcT backend transpiler to C++")
    parser.add_argument("infile", help="path to file to be copiled [preffered .tmb]")
    parser.add_argument("-o", "--output", help="Output to target file")
    # intentionally store default a something which is not a valid namespace
    parser.add_argument("-m", "--as-module", type=str, default=invalid_namespace, help="return C++ headeer instead of normal program")
    args = parser.parse_args(argv)

    base, _ = os.path.splitext(args.infile)
    outfile = args.output or base + ".cpp"

    # 1. Read input Timber source file
    try:
        with open(args.infile) as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.infile}' not found.", file=sys.stderr)
        sys.exit(1)

        # 2. Parse source string directly from memory (Instant & Safe!)
    p = Parser(raw)
    ast = p.parse()

    # 2.5 analyse the program
    verify(ast)

        # 3. Code Generation Emit
    cpp = emit_module(ast, as_module=args.as_module != invalid_namespace, module_name=args.as_module)
    with open(outfile, "w") as f:
            f.write(cpp)
    print(f"{args.infile} -> {outfile}")

    # 4. Handle structural temp file output ONLY if debug extraction flag is explicitly enabled


if __name__ == "__main__":
    main()
