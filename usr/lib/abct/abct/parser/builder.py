# parser/builder.py
from .statement import StatementParser
from .lexer import TokenType
from ..abct_ast.node import Module

class Parser(StatementParser):
    def parse(self) -> Module:
        """Entry point of the parser: start: stmt+"""
        stmts = []
        while self.current_token.type != TokenType.EOF:
            if self.match(TokenType.SEMI):
                continue
            stmts.append(self.parse_statement())
        return Module(stmts=stmts)
