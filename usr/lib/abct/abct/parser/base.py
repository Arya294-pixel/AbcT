# parser/base.py
from .lexer import Lexer, TokenType, Token
from copy import deepcopy

class AbcTSyntaxError(SyntaxError):
    """Custom exception that prints a visual error pointer in the terminal."""
    def __init__(self, message: str, token: Token, source_lines: list[str]):
        self.message = message
        self.token = token
        line_idx = token.line - 1
        src_line = source_lines[line_idx] if line_idx < len(source_lines) else ""
        pointer = " " * (token.column - 1) + "^"
        
        error_report = (
            f"\n[AbcT Syntax Error] {message}\n"
            f"  --> Line {token.line}, Col {token.column}\n"
            f"    |\n"
            f"    |  {src_line}\n"
            f"    |  {pointer}\n"
        )
        super().__init__(error_report)

class BaseParser:
    def __init__(self, source: str):
        self.source_lines = source.splitlines()
        self.lexer = Lexer(source)
        
        # Populate tokens list from the lexer
        self.tokens = []
        while True:
            token = self.lexer.next_token()
            self.tokens.append(token)
            if token.type == TokenType.EOF: break
            
        self.pos = 0
        self.current_token = self.tokens[self.pos]

    @property
    def peek_token(self):
        return self.peek_token_at(1)

    def peek_token_at(self, offset:int):
        tpos = self.pos + offset
        if tpos < len(self.tokens) :
            return self.tokens[tpos]
        else:
            return self.tokens[-1]

    def advance(self):
        if self.pos < len(self.tokens) -1:
            self.pos += 1
        else:
            return
        self.current_token = self.tokens[self.pos]
        
    def check(self, *expected_types):
        return self.current_token.type in expected_types

    def match(self, *types: TokenType) -> bool:
        if self.check(*types):
            self.advance()
            return True
        return False

    def consume(self, expected_type: TokenType, err_msg: str) -> Token:
        if self.check(expected_type):
            tok = self.current_token
            self.advance()
            return tok
        raise AbcTSyntaxError(err_msg, self.current_token, self.source_lines)

    def clearnext(self, expected_type: TokenType):
        """consumes all token matching the type"""
        while self.match(expected_type):
            pass

    def error(self, message: str):
        raise AbcTSyntaxError(message, self.current_token, self.source_lines)
