# parser/base.py
from .lexer import Lexer, TokenType, Token

class AbcTSyntaxError(SyntaxError):
    """Custom exception that prints a visual error pointer in the terminal."""
    def __init__(self, message: str, token: Token, source_lines: list[str]):
        self.message = message
        self.token = token
        line_idx = token.line - 1
        src_line = source_lines[line_idx] if line_idx < len(source_lines) else ""
        pointer = " " * (token.column - 1) + "^"
        
        error_report = (
            f"\n[Timber Syntax Error] {message}\n"
            f"  --> Line {token.line}, Col {token.column}\n"
            f"    |\n"
            f"    |  {src_line}\n"
            f"    |  {pointer}\n"
        )
        super().__init__(error_report)

TimberSyntaxError = AbcTSyntaxError

class BaseParser:
    def __init__(self, source: str):
        self.source_lines = source.splitlines()
        self.lexer = Lexer(source)
        self.current_token: Token = self.lexer.next_token()
        self.peek_token: Token = self.lexer.next_token()

    def advance(self):
        self.current_token = self.peek_token
        if self.current_token.type != TokenType.EOF:
            self.peek_token = self.lexer.next_token()

    def check(self, expected_type: TokenType) -> bool:
        return self.current_token.type == expected_type

    def match(self, *types: TokenType) -> bool:
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, expected_type: TokenType, err_msg: str) -> Token:
        if self.check(expected_type):
            tok = self.current_token
            self.advance()
            return tok
        raise TimberSyntaxError(err_msg, self.current_token, self.source_lines)

    def error(self, message: str):
        raise TimberSyntaxError(message, self.current_token, self.source_lines)
