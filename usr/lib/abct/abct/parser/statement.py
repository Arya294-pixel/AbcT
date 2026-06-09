# parser/statement.py
from .expression import ExpressionParser
from .lexer import TokenType
from ..abct_ast.node import *

# utilities

def get_mangle_Template(name, params, capabilities):
    # Sort capabilities for canonical order
    sorted_caps = sorted(capabilities)
    
    # Use 0X_0 as the separator
    cap_str = "0X_0".join(sorted_caps)
    
    # Construct the mangle string
    return f"_M15{len(name)}{name}Template{len(params)}{params[0]}0X_0{cap_str}_abcT"



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
    def parse_statement(self) -> Node:
        while self.match(TokenType.SEMI):pass
        if self.match(TokenType.TEMPLATE) or self.check(TokenType.LT): return self.parse_template_stmt()
        if self.match(TokenType.IMPORT): return self.parse_import_stmt()
        if self.match(TokenType.TEMPLATE): return self.parse_template_stmt()
        if self.match(TokenType.IF): return self.parse_if_stmt()
        if self.match(TokenType.WHILE): return self.parse_while_stmt()
        if self.match(TokenType.DO): return self.parse_do_while_stmt()
        if self.match(TokenType.ITER): return self.parse_iter_stmt()
        if self.match(TokenType.CLASS): return self.parse_class_def()
        if self.match(TokenType.FN): return self.parse_func_def()
        if self.match(TokenType.RETURN): return self.parse_return_stmt()
        if self.match(TokenType.PASS): return self.parse_pass_stmt()
        if self.match(TokenType.BREAK): return self.parse_break_stmt()
        if self.match(TokenType.CONTINUE):
            self.consume(TokenType.SEMI, "Expected ';' after continue.")
            return Continue()
        if self.current_token.type == TokenType.NAME and self.peek_token.type == TokenType.COLON: return self.parse_AnnAssign()
        self.error("unexpected keyword found: " +str(self.peek_token))
    def parse_AnnAssign(self):
        target_name = self.current_token.value
        self.advance()  # Consume NAME
        self.advance()  # Consume COLON
        if self.current_token.type != TokenType.NAME:
            self.error(f"invlid token found: {self.current_token}")
        type_str, depth = self.parse_type()
        pointer = False
        if type_str.endswith("*"):
            pointer = True
            ptr_length = type_str.count("*")
            type_str = type_str.replace("*", "")
        full_annotation = type_str + ("[]" * depth)
        if pointer:
            full_annotation += "*" * ptr_length
            
        value_node = None
        if self.match(TokenType.ASSIGN):
            value_node = self.parse_expression()
        self.consume(TokenType.SEMI, "Expected ';' after declaration.")
        return AnnAssign(target=target_name, annotation=full_annotation, value=value_node)

        # Fallback to standard assignments or naked expression statements
        expr_node = self.parse_expression()
        if self.match(TokenType.ASSIGN):
            value_node = self.parse_expression()
            self.consume(TokenType.SEMI, "Expected ';' after assignment.")
            return Assign(target=expr_node, value=value_node)
            
        self.consume(TokenType.SEMI, "Expected ';' after expression statement.")
        return Expr(value=expr_node)

    def parse_template_stmt(self) -> Node:
        def inline_iterator_hanldler(i):
            try:
                iter(i)
                return i
            except:
                return [i]
        templates_ = self.parse_template_header()
        if self.match(TokenType.CLASS):
            return self.parse_class_def(existing_templates=templates_)
        elif self.match(TokenType.FN):
            return self.parse_func_def(existing_templates=templates_)

        templates = []
        for template in inline_iterator_hanldler(templates_):
            templates.append(TemplateDef(template))
        return templates

    def parse_func_def(self, existing_templates=None) -> FuncDef:
        templates = existing_templates or []
        # 1. Parse optional Template Headers (if nested)
        if self.match(TokenType.TEMPLATE):
            templates = self.parse_template_header()

        # 2. Parse Name and Parameters
        name = Name(id=self.consume(TokenType.NAME, "Expected name").value)
        self.consume(TokenType.LPAREN, "Expected '('")

        params = []
        if not self.check(TokenType.RPAREN):
            while True:
                p_name = self.consume(TokenType.NAME, "Param name?").value
                self.consume(TokenType.COLON, "Expected ':'")
                t_str, _ = self.parse_type()
                
                # Resolve: If name is in templates, it is a TemplateRef
                is_t = any(t.name.id == t_str for t in templates)
                node = TemplateRef(Name(t_str)) if is_t else TypeRef(Name(t_str))
                params.append((p_name, node))
                
                if not self.match(TokenType.COMMA): break
        
        self.consume(TokenType.RPAREN, "Expected ')'")
        self.consume(TokenType.ARROW, "Expected '->'")
        
        # 3. Resolve Return Type
        ret_str, _ = self.parse_type()
        is_ret_t = any(t.name.id == ret_str for t in templates)
        ret_node = TemplateRef(Name(ret_str)) if is_ret_t else TypeRef(Name(ret_str))

        # 4. Parse Body
        self.consume(TokenType.LBRACE, "Expected '{'")
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())
        self.consume(TokenType.RBRACE, "Expected '}'")

        return FuncDef(
            name=name,
            params=params, 
            templates=templates,
            body=body,
            ret=ret_node
        )

    def parse_class_def(self, existing_templates=None) -> ClassDef:
        # 1. Parse optional Template Headers
        templates = existing_templates or []
        if self.match(TokenType.TEMPLATE):
            templates = self.parse_template_header()

        # 2. Parse Class Name
        class_name_str = self.consume(TokenType.NAME, "Expected class name.").value
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
            if self.match(TokenType.FN):
                # Pass existing class-level templates down to methods
                method_node = self.parse_func_def(existing_templates=templates)
                if current_visibility == TokenType.PUBLIC: 
                    public_methods.append(method_node)
                else: 
                    private_methods.append(method_node)
                continue
            
            # Attribute parsing
            if self.current_token.type == TokenType.NAME and self.peek_token == TokenType.COLON:
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

        return ClassDef(
            name=class_name_node,
            public_attributes=public_attrs,
            private_attributes=private_attrs,
            public_methods=public_methods,
            private_methods=private_methods,
            templates=templates # No more template_params here!
        )


    def parse_import_stmt(self) -> Import:
        """Parses: import <module_name>;"""
        # The 'import' keyword has already been matched and consumed by self.match()
        module_token = self.consume(TokenType.NAME, "Expected module namespace name identifier.")
        module_name = module_token.value
        
        # Enforce your strict semicolon design specification rule
        self.consume(TokenType.SEMI, "Expected ';' after import statement.")
        
        # Cache the identifier string into our compilation context collection
        self.imported_modules.add(module_name)
        
        # Return a cleanly structured AST block node back up to the collector array
        return Import(source=Name(id=module_name))

    def parse_type(self) -> tuple[str, int]:
        type_token = self.consume(TokenType.NAME, "Expected type name.")
        type_name = type_token.value
        while self.match(TokenType.MUL):
            type_name += "*"
        depth = 0
        while self.match(TokenType.LBRACK):
            self.consume(TokenType.RBRACK, "Expected closing ']' in type signature.")
            depth += 1
        return type_name, depth

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

    def parse_while_stmt(self) -> While:
        test = Cond(expr=self.parse_expression())
        self.consume(TokenType.LBRACE, "Expected '{' after while condition.")
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())
        self.consume(TokenType.RBRACE, "Expected '}' after while body.")
        return While(test=test, body=body)

    def parse_do_while_stmt(self) -> For:
        self.consume(TokenType.LBRACE, "Expected '{' after do keyword.")
        body = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())
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
