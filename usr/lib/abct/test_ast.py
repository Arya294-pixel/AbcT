from abct.parser.statement import StatementParser
from abct.parser.lexer import Lexer, TokenType
from pprint import pprint

def run_parser_test(source_code):    
    # 2. Setup the Parser (Your StatementParser expects a list/iterable of tokens)
        parser = StatementParser(source_code)
    
    # 3. Parse and catch output
        print(f"--- Parsing: {source_code.strip()} ---")
        node = parser.parse_statement()
        print(node)        

codes = ["""
class foo {
    public:
        val: int;
}

fn bar() -> int {
    return 0;
}
""",
"""
template <typename T:(Any)> class container {
    public:
        data: T;
}

template <typename T:(Any)> fn process() -> void {
    pass;
}
""",
"template<typename T>",
"""
class processor {
    public:
        <typename T:(Any)> fn execute(input: T) -> T {
            return input;
        }
}
"""

]


for code in codes:
    print(code)
    run_parser_test(code)
