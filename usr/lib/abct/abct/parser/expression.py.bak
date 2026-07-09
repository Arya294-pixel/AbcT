# parser/expression.py
from .base import BaseParser
from .lexer import TokenType
from ..abct_ast.node import *

class ExpressionParser(BaseParser):
    def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         self.ensure_attribute("imported_modules", set())

    def ensure_attribute(self, attr, default):
         if not hasattr(self, attr):
             setattr(self, attr, default)

    def parse_expression(self) -> Node:
        return self.parse_or()

    def parse_or(self) -> Node:
        node = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            node = Compare(left=node, op="||", right=right)
        return node

    def parse_and(self) -> Node:
        node = self.parse_cmp()
        while self.match(TokenType.AND):
            right = self.parse_cmp()
            node = Compare(left=node, op="&&", right=right)
        return node

    def parse_cmp(self) -> Node:
        node = self.parse_add()
        comp_ops = {
            TokenType.EQ: "==", TokenType.NEQ: "!=",
            TokenType.LT: "<", TokenType.LE: "<=",
            TokenType.GT: ">", TokenType.GE: ">="
        }
        if self.current_token.type in comp_ops:
            op_tok = self.current_token
            self.advance()
            right = self.parse_add()
            node = Compare(left=node, op=comp_ops[op_tok.type], right=right)
        return node

    def parse_add(self) -> Node:
        node = self.parse_mul()
        while self.current_token.type in (TokenType.ADD, TokenType.SUB):
            op_tok = self.current_token
            self.advance()
            right = self.parse_mul()
            node = BinOp(left=node, op=op_tok.value, right=right)
        return node

    def parse_mul(self) -> Node:
        node = self.parse_unary()
        while self.current_token.type in (TokenType.MUL, TokenType.DIV, TokenType.MOD):
            op_tok = self.current_token
            self.advance()
            right = self.parse_unary()
            node = BinOp(left=node, op=op_tok.value, right=right)
        return node

    def parse_unary(self) -> Node:
        if self.current_token.type in (TokenType.ADD, TokenType.SUB, TokenType.NOT, TokenType.INV, TokenType.AMPERSTAND,TokenType.MUL):
            op_tok = self.current_token
            self.advance()
            operand = self.parse_unary()
            op_str = op_tok.value
            if op_tok.type == TokenType.AMPERSTAND:
                op_str = "address_of"
            elif op_tok.type == TokenType.MUL:
                op_str = "deref"
            return UnaryOp(op=op_str, operand=operand)
        return self.parse_postfix()

    def parse_postfix(self) -> Node:
        module_cache = getattr(self, "imported_modules", set())
        node = self.parse_atom()
        while True:
            if self.match(TokenType.LBRACK):
                expr = self.parse_expression()
                self.consume(TokenType.RBRACK, "Expected closing ']' after array index accessor.")
                base_depth = getattr(node, 'depth', 0)
                node = Subscript(value=node, index=expr, depth=max(0, base_depth - 1))
                
            elif self.match(TokenType.LPAREN):
                args = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expression())
                self.consume(TokenType.RPAREN, "Expected closing ')' after arguments call.")
                node = Call(func=node, args=args)
                
            elif self.match(TokenType.DOUBLE_COLON):
                if self.match(TokenType.LT):
                    targs = []
                    targs.append(self.consume(TokenType.NAME, "Expected template type argument name.").value)
                    while self.match(TokenType.COMMA):
                        targs.append(self.consume(TokenType.NAME, "Expected template type argument name.").value)
                    self.consume(TokenType.GT, "Expected closing '>' template operator bounds bracket.")
                    
                    self.consume(TokenType.LPAREN, "Expected open parenthetical signature block initialization.")
                    args = []
                    if not self.check(TokenType.RPAREN):
                        args.append(self.parse_expression())
                        while self.match(TokenType.COMMA):
                            args.append(self.parse_expression())
                    self.consume(TokenType.RPAREN, "Expected closing parameter argument parenthesis.")
                    node = TemplateCall(func=node, targs=targs, args=args)
                else:
                    attr_tok = self.consume(TokenType.NAME, "Expected field identifier target name after '::'.")
                    node = Attribute(value=node, attr=attr_tok.value, kind=AttrKind.STATIC)
                    
            elif self.match(TokenType.DOT):
                attr_tok = self.consume(TokenType.NAME, "Expected property label identity after '.'.")
                attrkind = AttrKind.MEMBER

                if isinstance(node, Name):
                    if node.id in module_cache:
                        attrkind = AttrKind.NAMESPACE

                node = Attribute(value=node, attr=attr_tok.value, kind=attrkind)
            elif self.match(TokenType.ARROW):
                print("[DEBUG]: ARROW token found. emiiting as attribute")
                attr_tok = self.consume(TokenType.NAME, "Expected property label identity after '->'.")
                node = Attribute(value=node, attr=attr_tok.value, kind=AttrKind.POINTER)
            else:
                break
        return node

    def parse_atom(self) -> Node:
        if self.match(TokenType.TRUE): return Const(value=True)
        if self.match(TokenType.FALSE): return Const(value=False)
        
        if self.check(TokenType.NUMBER):
            val = self.current_token.value
            self.advance()
            num = float(val) if '.' in val or 'e' in val.lower() else int(val, 0)
            return Const(value=num)
            
        if self.check(TokenType.STRING):
            val = self.current_token.value
            self.advance()
            return Const(value=val)
            
        if self.match(TokenType.LBRACK):
            elts = []
            if not self.check(TokenType.RBRACK):
                elts.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    elts.append(self.parse_expression())
            self.consume(TokenType.RBRACK, "Expected closing square bracket for array literal.")
            return Array(depth=1, elts=elts)
            
        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected matching closing parenthesis.")
            return expr
            
        if self.check(TokenType.NAME):
            name_tok = self.current_token
            self.advance()
            return Name(id=name_tok.value, depth=0)
            
        self.error(f"Invalid expression component token parsed: '{self.current_token.value}'")
