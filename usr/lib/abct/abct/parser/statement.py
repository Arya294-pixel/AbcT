# parser/statement.py
import re # for type extraction
from .expression import ExpressionParser
from .lexer import TokenType
from ..abct_ast.node import *
from logging import info

info = print
# utilities

class Set(set):
    def __hash__(self):
        return id(self)


class StatementParser(ExpressionParser):
    FORBIDDEN_IN_CLASS = {
        TokenType.IMPORT, 
        TokenType.IF, 
        TokenType.WHILE,
        TokenType.DO, 
        TokenType.ITER, 
        TokenType.RETURN,
        TokenType.PASS,
        TokenType.BREAK,
        TokenType.CONTINUE
    }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ensure_attribute("current_class_templates", Set())
        
    def parse_statement(self) -> Node:
        while self.match(TokenType.SEMI):pass
        print("[DDBUG] STMT:", self.current_token)
        if self.match(TokenType.TEMPLATE) or self.check(TokenType.LT): return self.parse_template_stmt()
        if self.match(TokenType.IMPORT): return self.parse_import_stmt()
        if self.match(TokenType.INCLUDE): return self.parse_include_stmt()
        if self.match(TokenType.TEMPLATE): return self.parse_template_stmt()
        if self.match(TokenType.IF): return self.parse_if_stmt()
        if self.match(TokenType.WHILE): return self.parse_while_stmt()
        if self.match(TokenType.DO): return self.parse_do_while_stmt()
        if self.match(TokenType.ITER): return self.parse_iter_stmt()
        if self.match(TokenType.CLASS): return self.parse_class_def()
        if self.match(TokenType.FN): return self.parse_func_def()
        if self.match(TokenType.TRY): return self.parse_try_catch()
        if self.match(TokenType.RETURN): return self.parse_return_stmt()
        if self.match(TokenType.PASS): return self.parse_pass_stmt()
        if self.match(TokenType.BREAK): return self.parse_break_stmt()
        if self.match(TokenType.CONTINUE):
            self.consume(TokenType.SEMI, "Expected ';' after continue.")
            return Continue()
        if self.current_token.type == TokenType.NAME:
            if self.peek_token_at(1).type == TokenType.COLON:
                return self.parse_AnnAssign()
            elif self.peek_token_at(1).type == TokenType.ASSIGN:
                return self.parse_Assign()
            expr = self.parse_expression()
            if isinstance(expr, (Assign, AnnAssign)):
                return expr
            return Expr(value=expr)
        self.error("unexpected keyword found: " +str(self.current_token))

    def parse_template_stmt(self) -> Node:
        def inline_iterator_hanldler(i):
            try:
                iter(i)
                return i
            except:
                return [i]
        templates_ = self.parse_template_header()
        self.clearnext(TokenType.SEMI)
        if self.match(TokenType.CLASS):
            return self.parse_class_def(existing_templates=templates_)
        elif self.match(TokenType.FN):
            return self.parse_func_def(existing_templates=templates_)

        return templates_ 

    def parse_func_def(self, existing_templates=None) -> FuncDef:
        templates = existing_templates or []
        # 1. Parse optional Template Headers (if nested)
        if self.match(TokenType.TEMPLATE):
            templates = self.parse_template_header()

        # 2. Parse Name, Parameters, flags
        readonly = False
        if self.match(TokenType.READONLY):
            readonly = True
        name = Name(id=self.consume(TokenType.NAME, "Expected name").value)
        self.consume(TokenType.LPAREN, "Expected '('")

        params = []
        if not self.check(TokenType.RPAREN):
            while True:
                p_name = self.consume(TokenType.NAME, "Param name?").value
                self.consume(TokenType.COLON, "Expected ':'")
                p_type = self.parse_type()
                params.append((p_name, p_type))
                
                if not self.match(TokenType.COMMA): break
        
        self.consume(TokenType.RPAREN, "Expected ')'")
        self.consume(TokenType.ARROW, "Expected '->'")
        
        # 3. Resolve Return Type
        ret_node = self.parse_type()

        # 4. Parse Body
        self.consume(TokenType.LBRACE, "Expected '{'")
        body = []
        print(f"LOOP(BEFORE): {self.check}")
        while not (self.check(TokenType.RBRACE) or self.check(TokenType.EOF)):
            while self.match(TokenType.SEMI): pass
            if self.check(TokenType.RBRACE): break
            self.clearnext(TokenType.SEMI)
            print(f"LOOP: {self.current_token}")
            body.append(self.parse_statement())
        self.consume(TokenType.RBRACE, "Expected '}'")

        return FuncDef(
            name=name,
            params=params, 
            templates=templates,
            body=body,
            ret=ret_node,
            readonly=readonly
        )

    def parse_class_def(self, existing_templates=None) -> ClassDef:
        # 1. Parse optional Template Headers
        templates = existing_templates or []
        old_templates = self.current_class_templates
        self.current_class_templates.update(Set({*templates}))
        self.current_class_templates = Set(self.current_class_templates)
        if self.match(TokenType.TEMPLATE):
            templates = self.parse_template_header()
            self.current_class_templates.update(templates)
        print(self.current_class_templates)
        # 2. Parse Class Name
        bases = []
        class_name_str = self.consume(TokenType.NAME, "Expected class name.").value
        print(f"parsing base started. current token: {self.current_token}, peek: {self.peek_token}")
        if self.match(TokenType.LPAREN):
            while not self.match(TokenType.RPAREN):
                bases.append(
                    Name(
                        id=self.consume(TokenType.NAME, "Expected ')' or name of the class").value
                    )
                )
                if self.match(TokenType.RPAREN):
                    break
                else:
                    self.consume(TokenType.COMMA, "Expected ',' between two class names")
        class_name_node = Name(id=class_name_str)

        self.consume(TokenType.LBRACE, "Expected '{' to start class body.")

        public_attrs, private_attrs = [], []
        public_methods, private_methods = [], []
        current_visibility = TokenType.PUBLIC

        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            while self.match(TokenType.SEMI): pass
            
            # Visibility modifiers
            if self.match(TokenType.PUBLIC):
                self.consume(TokenType.COLON, "Expected ':'")
                current_visibility = TokenType.PUBLIC
                continue
            elif self.match(TokenType.PRIVATE):
                self.consume(TokenType.COLON, "Expected ':'")
                current_visibility = TokenType.PRIVATE
                continue

            # Method parsing
            annassign = False
            if self.match(TokenType.FN):
                # Pass existing class-level templates down to methods
                method_node = self.parse_func_def(existing_templates=templates)
                if isinstance(method_node, AnnAssign):
                    annassign = True
                elif current_visibility == TokenType.PUBLIC: 
                    public_methods.append(method_node)
                else: 
                    private_methods.append(method_node)
                continue
            
            # Attribute parsing
            if (self.current_token.type == TokenType.NAME and self.peek_token == TokenType.COLON) or annassign:
                if annassign:
                    node = method_node
                else:
                    node = self.parse_AnnAssign()
                if current_visibility == TokenType.PUBLIC:
                    public_attrs.append(node)
                else:
                    private_attrs.append(node)
            
            elif self.check(TokenType.RBRACE):
                break
            else:
                if self.peek_token.type in self.FORBIDDEN_IN_CLASS:
                    self.error(f"use of {self.peek_token} is forbidden inside a class scope")
                node = self.parse_statement()
                if current_visibility == TokenType.PRIVATE:
                    private_attrs.append(node)
                else:
                    public_methods.append(node)

        self.consume(TokenType.RBRACE, "Expected '}'")
        self.current_class_templates = old_templates

        _public_methods, _public_attributes = [], []
        _private_methods, _private_attributes = [], []

        for elemnt in private_methods + private_attrs:
            if isinstance(elemnt, AnnAssign):
                _private_attributes.append(elemnt)
            else:
                _private_methods.append(elemnt)

        for elemnt in public_methods + public_attrs:
            if isinstance(elemnt, AnnAssign):
                _public_attributes.append(elemnt)
            else:
                _public_methods.append(elemnt)

        return ClassDef(
            name=class_name_node,
            bases=bases or [Name(id="Object")],
            public_attributes=_public_attributes,
            private_attributes=_private_attributes,
            public_methods=_public_methods,
            private_methods=_private_methods,
            templates=templates
        )

    def parse_import_stmt(self):
        module = self.consume(
            TokenType.STRING,
            "Expected module name."
        ).value
        self.consume(TokenType.SEMI, "Expected ';'.")
        return Import(source=module)

    def parse_include_stmt(self):
        module = self.consume(
            TokenType.STRING,
            "Expected module name."
        ).value
        self.consume(TokenType.SEMI, "Expected ';'.")
        return Include(source=module)

    def parse_type_atom(self) -> Type:
        name = self.consume(
            TokenType.NAME,
            "Expected type name."
        ).value

        if any(
            t.name.id == name
            for t in self.current_class_templates
        ):
            node = TemplateRef(
                name=Name(id=name)
            )
        else:
            node = TypeRef(
                name=Name(id=name)
            )

        if self.match(TokenType.LT):
            args = []

            if not self.check(TokenType.GT):
                args.append(
                    self.parse_type()
                )

                while self.match(TokenType.COMMA):
                    args.append(
                        self.parse_type()
                    )

            self.consume(
                TokenType.GT,
                "Expected '>' after template arguments."
            )

            node = TemplateType(
                target=node,
                args=args
            )

        return node

    def parse_type(self) -> Type:
        readonly = self.match(TokenType.READONLY)
        node = self.parse_type_atom()
        while True:
            if self.match(TokenType.MUL):
                node = PtrType(target=node)

            elif self.match(TokenType.AMPERSTAND):
                node = RefType(target=node)

            elif self.match(TokenType.AND):
                node = RValueRefType(target=node)

            elif self.match(TokenType.LBRACK):
                self.consume(
                    TokenType.RBRACK,
                    "Expected closing ']' in array type."
                )
                node = ArrayType(target=node)

            elif self.match(TokenType.LT):
                args = []

                if not self.check(TokenType.GT):
                    args.append(self.parse_type())

                    while self.match(TokenType.COMMA):
                        args.append(self.parse_type())

                self.consume(
                    TokenType.GT,
                    "Expected '>' after template arguments."
                )

                node = TemplateType(
                    target=node,
                    args=args
                )

            else:
                break
        if readonly:
            return ConstType(target=node)
        return node

    def parse_template_header(self) -> list[TemplateDef]:
        templates = []
        self.consume(TokenType.LT, "Expected '<'")
        while True:
            self.consume(TokenType.TYPENAME, "Expected 'typename'")
            t_name = self.consume(TokenType.NAME, "Expected template name").value
        
            cap = [TemplateCapablity.ANY]
            if self.match(TokenType.COLON):
                self.consume(TokenType.LPAREN, "Expected '('")
                cap_name = self.consume(TokenType.NAME, "expected capability").value
                # Map string to Enum here
                cap = [TemplateCapablity[cap_name.upper()]] 
                self.consume(TokenType.RPAREN, "Expected ')'")

            # FIX: Store as TemplateDef object
            templates.append(TemplateDef(name=Name(id=t_name), capablity=cap))

            if not self.match(TokenType.COMMA): break
    
        if self.check(TokenType.GT): self.consume(TokenType.GT, "Expected '>'")
        elif self.match(TokenType.GT): pass
        return templates

    """
    def parse_if_stmt(self) -> If:
        test = self.parse_expression()
        self.consume(TokenType.LBRACE, "Expected '{' after if condition.")
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())
        self.consume(TokenType.RBRACE, "Expected '}' after if body.")

        orelse = []
        if self.match(TokenType.ELIF):
            # Recurse directly into an If statement and store it as a statement in orelse
            orelse.append(self.parse_if_stmt())
        elif self.match(TokenType.ELSE):
            self.consume(TokenType.LBRACE, "Expected '{' after else keyword.")
            while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
                orelse.append(self.parse_statement())
            self.consume(TokenType.RBRACE, "Expected '}' after else body.")

        return If(test=test, body=body, orelse=orelse if orelse else None)
    """
    def parse_if_stmt(self) -> If:
        # 1. Parse the condition
        # (Assuming parse_expression handles surrounding '(' and ')')
        test = self.parse_expression()
        print(f"{test = }")
        
        # 2. Consume mandatory LBRACE
        self.consume(TokenType.LBRACE, "Expected '{' after if condition.")
        
        # 3. Parse IF body
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            # If we see ELSE or ELIF, the if-body is over
            if self.check(TokenType.ELSE, TokenType.ELIF):
                break
            body.append(self.parse_statement())
            while self.match(TokenType.SEMI): pass
            print(f"[DEBUG] (parse_if_stmt): {self.current_token = }, {self.peek_token = }")
        print(self.current_token, self.peek_token)
        self.consume(TokenType.RBRACE, "Expected '}' after if body.")
        
        # 4. Handle ELIF / ELSE
        orelse = []
        if self.match(TokenType.ELIF):
            # Recurse: Elif is just another If statement
            orelse.append(self.parse_if_stmt())
        elif self.match(TokenType.ELSE):
            self.consume(TokenType.LBRACE, "Expected '{' after else keyword.")
            while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
                orelse.append(self.parse_statement())
            self.consume(TokenType.RBRACE, "Expected '}' after else body.")

        return If(test=test, body=body, orelse=orelse if orelse else None)


    def parse_while_stmt(self) -> While:
        test = Cond(expr=self.parse_expression())
        self.consume(TokenType.LBRACE, "Expected '{' after while condition.")
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())
            while self.match(TokenType.SEMI): pass
        self.consume(TokenType.RBRACE, "Expected '}' after while body.")
        return While(test=test, body=body)

    def parse_do_while_stmt(self) -> For:
        self.consume(TokenType.LBRACE, "Expected '{' after do keyword.")
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):        
            body.append(self.parse_statement())
            while self.match(TokenType.SEMI): pass
            if self.current_token.type == TokenType.RBRACE:
                break
        self.consume(TokenType.RBRACE, "Expected '}' after do body.")
        self.consume(TokenType.WHILE, "Expected 'while' keyword after do block.")
        test = Cond(expr=self.parse_expression())
        self.consume(TokenType.SEMI, "Expected terminating ';' after do-while condition.")
        return For(header=(None, test, None), body=body)

    def parse_iter_stmt(self) -> Iter:
        iterable = self.parse_expression()
        var_name = self.consume(TokenType.NAME, "Expected iterator variable name.").value
        self.consume(TokenType.LBRACE, "Expected '{' after iterator block start.")
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())
        self.consume(TokenType.RBRACE, "Expected '}' after iter body.")
        return Iter(iterable=iterable, var=var_name, body=body)

    def parse_try_catch(self) -> TryCatch:
        # Parse try body
        self.consume(
            TokenType.LBRACE,
            "Expected '{' after try."
        )

        try_body = []

        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            try_body.append(self.parse_statement())
            self.clearnext(TokenType.SEMI)

        self.consume(
            TokenType.RBRACE,
            "Expected '}' after try body."
        )

        # Parse one or more catch blocks
        catch_blocks = []

        while self.match(TokenType.CATCH):
            exception_type = None

            # catch { ... } -> catch all exceptions
            #
            # catch SomeError { ... }
            # catch exception<std::string> { ... }
            #       ^^^^^^^^^^^^^^^^^^^^^
            #       parsed by parse_type()
            if not self.check(TokenType.LBRACE):
                exception_type = self.parse_type()

            self.consume(
                TokenType.LBRACE,
                "Expected '{' after catch type."
            )

            body = []

            while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
                body.append(self.parse_statement())
                self.clearnext(TokenType.SEMI)

            self.consume(
                TokenType.RBRACE,
                "Expected '}' after catch body."
            )

            catch_blocks.append(
                CatchBlock(
                    exception_type=exception_type,
                    body=body
                )
            )

        # A try must have at least one catch block.
        if not catch_blocks:
            self.error("Expected 'catch' after try block.")

        return TryCatch(
            try_body=try_body,
            catch_blocks=catch_blocks
        )

    def parse_throw_stmt(self) -> Throw:
        val = self.parse_expression()
        self.consume(TokenType.SEMI, "Expected ';' after throw statement.")
        return Throw(value=val)

    def parse_return_stmt(self) -> Return:
        val = None
        if not self.check(TokenType.SEMI):
            val = self.parse_expression()
        self.consume(TokenType.SEMI, "Expected ';' after return value statement.")
        return Return(value=val)

    def parse_pass_stmt(self) -> Pass:
        self.consume(TokenType.SEMI, "Expected ';' after pass.")
        return Pass()

    def parse_break_stmt(self) -> Break:
        level = 1
        if self.check(TokenType.NUMBER):
            level = int(self.current_token.value, 0)
            self.advance()
        self.consume(TokenType.SEMI, "Expected ';' after break statement.")
        return Break(level=level)
