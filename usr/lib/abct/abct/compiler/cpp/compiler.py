#!/usr/bin/env python3
import argparse
import sys
import os

from abct.preparse.braces import colon_to_braces
from abct.parser.builder import Parser          # Swapped out Lark builder for our high-speed one
from abct.emit.cpp.stmt import emit_module
from abct.semamtics import verify

invalid_namespace = "$namespace$"

def main():
    parser = argparse.ArgumentParser("Timber backend transpiler to C++")
    parser.add_argument("infile", help="path to file to be copiled [preffered .tmb]")
    parser.add_argument("-o", "--output", help="Output to target file")
    parser.add_argument("--keep-temp", action="store_true", help="Preserve the formatted code string to disk for debugging")
    parser.add_argument("--C-style", action="store_true", help="treat the code as C style formatting")
    # intentionally store default a something which iant valid namespace
    parser.add_argument("-m", "--as-module", type=str, default=invalid_namespace, help="return C++ headeer instead of normal program")
    args = parser.parse_args()

    base, _ = os.path.splitext(args.infile)
    outfile = args.output or base + ".cpp"

    # 1. Read input Timber source file
    try:
        with open(args.infile) as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.infile}' not found.", file=sys.stderr)
        sys.exit(1)

    if not args.C_style:
        # Preparse layout formatting transformations
        formatted = colon_to_braces(raw)
    else:
        formatted = raw

    try:
        # 2. Parse source string directly from memory (Instant & Safe!)
        p = Parser(formatted)
        ast = p.parse()

        # 2.5 analyse the program
        verify(ast)

        # 3. Code Generation Emit
        cpp = emit_module(ast, as_module=args.as_module != invalid_namespace, module_name=args.as_module)
        with open(outfile, "w") as f:
            f.write(cpp)
        print(f"{args.infile} -> {outfile}")

    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        # If compilation fails, dump the debug tracker source to help identify line offsets
        if args.keep_temp:
            dump_debug_file(formatted)
        sys.exit(1)

    # 4. Handle structural temp file output ONLY if debug extraction flag is explicitly enabled
    if args.keep_temp:
        dump_debug_file(formatted)

def dump_debug_file(formatted_source: str):
    pid = os.getpid()
    prefix = os.environ.get("PREFIX", "/tmp")
    tmp_dir = os.path.join(prefix, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"abct{pid}.formatedtmb")
    
    with open(tmp_path, "w") as f:
        f.write(formatted_source)
    print(f"Temp source track written to: {tmp_path}")

if __name__ == "__main__":
    main()
