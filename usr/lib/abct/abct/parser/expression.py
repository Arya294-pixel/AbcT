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
        left = self.parse_or()
        peek_tokentype = self.peek_token.type # local cache for the type of next token. tbis is mainly done to increa the speed
        if peek_tokentype == TokenType.COLON:
            return self.parse_AnnAssign()
        elif self.match(TokenType.ASSIGN):
            right = self.parse_or()
            return Assign(
                target=left,
                value=right
            )
        return left
    def parse_Assign(self):
        target_name = self.current_token.value
        self.advance() # NAME
        self.consume(TokenType.ASSIGN, "expected '=' ")
        value_node = self.parse_expression()
        self.consume(TokenType.SEMI, "expected ';' after declaration")
        return Assign(
            target=Name(id=target_name),
            value = value_node
        )


    def parse_AnnAssign(self):
        target_name = self.consume(TokenType.NAME, "Expected name").value
        self.consume(TokenType.COLON, "Expected ':'")

        # 1. Parse the base type (returns string, depth)
        ann_node = self.parse_type()

        value_node = None
        if self.match(TokenType.ASSIGN):
            value_node = self.parse_expression()
        self.consume(TokenType.SEMI, "Expected ';' after declaration.")

        # Return the node instead of the 'full_annotation' string
        return AnnAssign(target=Name(id=target_name), annotation=ann_node, value=value_node)

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
#        print("entering parse_postfix. current token:", str(node))
        
        while True:
#            print("\t[DEBUG]:", node)
            # 1. Lookahead Guard: If the next token is not a postfix operator, 
            # we MUST stop. This allows the parser to return the 'node'
            # to the assignment or binary operator logic.
            if not self.check(TokenType.LBRACK, TokenType.LPAREN, TokenType.DOUBLE_COLON, 
                              TokenType.DOT, TokenType.ARROW):
                break

            # 2. Handle Subscripts
            if self.match(TokenType.LBRACK):
                expr = self.parse_expression()
                self.consume(TokenType.RBRACK, "Expected closing ']' after array index accessor.")
                base_depth = getattr(node, 'depth', 0)
                node = Subscript(value=node, index=expr, depth=max(0, base_depth - 1))

            # 3. Handle Calls
            elif self.match(TokenType.LPAREN):
                args = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expression())
                self.consume(TokenType.RPAREN, "Expected closing ')' after arguments call.")
                node = Call(func=node, args=args)

            # 4. Handle Static Access (::)
            elif self.match(TokenType.DOUBLE_COLON):
                if self.match(TokenType.LT):
                    # ... (TemplateCall logic remains the same)
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

            # 5. Handle Member/Namespace Access (.)
            elif self.match(TokenType.DOT):
                attr_tok = self.consume(TokenType.NAME, "Expected property label identity after '.'.")
                attrkind = AttrKind.MEMBER
                if isinstance(node, Name) and node.id in module_cache:
                    attrkind = AttrKind.NAMESPACE
                node = Attribute(value=node, attr=attr_tok.value, kind=attrkind)

            # 6. Handle Pointer Access (->)
            elif self.match(TokenType.ARROW):
                attr_tok = self.consume(TokenType.NAME, "Expected property label identity after '->'.")
                node = Attribute(value=node, attr=attr_tok.value, kind=AttrKind.POINTER)
            else:
                break
                
        return node

    def is_template_call(self) -> bool:
        """Peeks ahead to determine if '<' is the start of a generic type."""
        # Check the next few tokens for a '>' before a statement terminator
        for i in range(1, 10): 
            token = self.peek_token_at(i)
            if token.type == TokenType.GT: return True
            if token.type in (TokenType.SEMI, TokenType.LBRACE, TokenType.ASSIGN): return False
        return False

    def _parse_atom(self) -> Node:
        if self.match(TokenType.TRUE): return Const(value=True)
        if self.match(TokenType.FALSE): return Const(value=False)
        if self.check(TokenType.NUMBER):
            val = self.current_token.value
            self.advance()
            num = float(val) if '.' in val or 'e' in val.lower() else int(val, 0)
            return Const(value=num)

        if self.check(TokenType.STRING):
            value = self.current_token.value
            self.advance()
            return Const(value=value)
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
        return
    def parse_atom(self) -> Node:
        ret = self._parse_atom()
        if ret is not None:
            return ret
        if self.check(TokenType.NAME):
            name_tok = self.current_token
            self.advance()
            # Ambiguity Resolution: Only trigger template parsing if it's actually a template
            if self.check(TokenType.LT) and self.is_template_call():
                self.match(TokenType.LT) # Consume the '<'
                targs = []
                while True:
                    t_node = self.parse_type()
                    targs.append(t_node)
                    if self.match(TokenType.GT): break
                    self.consume(TokenType.COMMA, "Expected ',' or '>' in template list.")
                
                self.consume(TokenType.LPAREN, "Expected '(' for template constructor.")
                args = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expression())
                self.consume(TokenType.RPAREN, "Expected ')'")
                return TemplateCall(func=Name(id=name_tok.value), targs=targs, args=args)

            # Otherwise, it's just a Name; if it was followed by '<' but not a template, 
            # the parse_cmp() function handles the '<' comparison later.
            return Name(id=name_tok.value, depth=0)
