from enum import Enum, auto
from dataclasses import dataclass
import re

class TokenType(Enum):
    # Keywords
    FN = auto(); IF = auto(); ELIF = auto(); ELSE = auto(); WHILE = auto()
    DO = auto(); ITER = auto(); RETURN = auto(); PASS = auto(); BREAK = auto()
    CONTINUE = auto(); TRUE = auto(); FALSE = auto()
    IMPORT = auto();
    CLASS = auto();
    PRIVATE = auto(); PUBLIC = auto()
    TEMPLATE = auto(); TYPENAME = auto()

    # Literals & Identifiers
    NAME = auto(); NUMBER = auto(); STRING = auto()

    # Operators
    ASSIGN = auto()          # =
    EQ = auto(); NEQ = auto() # ==, !=
    LT = auto(); LE = auto()  # <, <=
    GT = auto(); GE = auto()  # >, >=
    ADD = auto(); SUB = auto() # +, -
    MUL = auto(); DIV = auto(); MOD = auto() # *, /, %
    AND = auto(); OR = auto()  # &&, ||
    NOT = auto(); INV = auto() # !, ~
    AMPERSTAND = auto(); # &
    STAR = MUL

    # Delimiters
    LPAREN = auto(); RPAREN = auto() # (, )
    LBRACE = auto(); RBRACE = auto() # {, }
    LBRACK = auto(); RBRACK = auto() # [, ]
    SEMI = auto()                    # ;
    COLON = auto(); DOUBLE_COLON = auto() # :, ::
    COMMA = auto()                   # ,
    DOT = auto(); ARROW = auto()     # .
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    KEYWORDS = {
        "fn": TokenType.FN, "if": TokenType.IF, "elif": TokenType.ELIF,
        "else": TokenType.ELSE, "while": TokenType.WHILE, "do": TokenType.DO,
        "iter": TokenType.ITER, "return": TokenType.RETURN, "pass": TokenType.PASS,
        "break": TokenType.BREAK, "continue": TokenType.CONTINUE,
        "true": TokenType.TRUE, "True": TokenType.TRUE,
        "false": TokenType.FALSE, "False": TokenType.FALSE,
        "import": TokenType.IMPORT, "class":TokenType.CLASS,
        "private": TokenType.PRIVATE, "public": TokenType.PUBLIC,
        "template":TokenType.TEMPLATE, "typename":TokenType.TYPENAME,
    }

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    def peek(self) -> str:
        if self.position >= self.length: return ""
        return self.source[self.position]

    def advance(self) -> str:
        char = self.peek()
        self.position += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def make_token(self, type: TokenType, value: str) -> Token:
        return Token(type, value, self.line, self.column - len(value))

    def next_token(self) -> Token:
        while self.position < self.length:
            char = self.peek()

            # Skip Whitespace
            if char.isspace():
                self.advance()
                continue

            # Skip Comments (# ...)
            if char == '#':
                while self.peek() != '\n' and self.position < self.length:
                    self.advance()
                continue

            # Multi-character Operators / Delimiters
            if char == '=':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    return self.make_token(TokenType.EQ, "==")
                return self.make_token(TokenType.ASSIGN, "=")

            if char == '!':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    return self.make_token(TokenType.NEQ, "!=")
                return self.make_token(TokenType.NOT, "!")

            if char == '<':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    return self.make_token(TokenType.LE, "<=")
                return self.make_token(TokenType.LT, "<")

            if char == '>':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    return self.make_token(TokenType.GE, ">=")
                return self.make_token(TokenType.GT, ">")

            if char == '&':
                self.advance()
                if self.peek() == '&':
                    self.advance()
                    return self.make_token(TokenType.AND, "&&")
                return self.make_token(TokenType.AMPERSTAND, "&&")
            if char == '|':
                self.advance()
                if self.peek() == '|':
                    self.advance()
                    return self.make_token(TokenType.OR, "||")
                raise SyntaxError(f"Unexpected character '|' at line {self.line}")

            if char == '-':
                self.advance()
                if self.peek() == '>':
                    self.advance()
                    return self.make_token(TokenType.ARROW, "->")
                return self.make_token(TokenType.SUB, "-")

            if char == ':':
                self.advance()
                if self.peek() == ':':
                    self.advance()
                    return self.make_token(TokenType.DOUBLE_COLON, "::")
                return self.make_token(TokenType.COLON, ":")

            # Single-character tokens (FIXED: dictionary keys match Enum variants)
            single_tokens = {
                '+': TokenType.ADD, '*': TokenType.MUL, '/': TokenType.DIV, '%': TokenType.MOD,
                '~': TokenType.INV, '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE, '[': TokenType.LBRACK,
                ']': TokenType.RBRACK, ';': TokenType.SEMI, ',': TokenType.COMMA, '.': TokenType.DOT
            }
            if char in single_tokens:
                self.advance()
                return self.make_token(single_tokens[char], char)

            # Strings
            if char in ('"', "'"):
                quote = self.advance()
                start_line, start_col = self.line, self.column - 1
                val = []
                while self.peek() != quote:
                    if self.position >= self.length:
                        raise SyntaxError(f"Unterminated string starting at line {start_line}")
                    c = self.advance()
                    if c == '\\':
                        val.append(self.advance())
                    else:
                        val.append(c)
                self.advance() # Consume closing quote
                decoded = bytes("".join(val), "utf-8").decode("unicode_escape")
                return Token(TokenType.STRING, decoded, start_line, start_col)

            # Numbers
            if char.isdigit():
                start = self.position
                while self.peek().isdigit() or self.peek() == '.':
                    self.advance()
                num_str = self.source[start:self.position]
                return self.make_token(TokenType.NUMBER, num_str)

            # Identifiers & Keywords
            if char.isalpha() or char == '_':
                start = self.position
                while self.peek().isalnum() or self.peek() == '_':
                    self.advance()
                lexeme = self.source[start:self.position]
                tok_type = self.KEYWORDS.get(lexeme, TokenType.NAME)
                return self.make_token(tok_type, lexeme)

            raise SyntaxError(f"Unknown character '{char}' at line {self.line}, col {self.column}")

        return Token(TokenType.EOF, "", self.line, self.column)
