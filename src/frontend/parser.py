"""
Phase 2c: Parser
------------------
Recursive descent parser. Each grammar rule from our spec becomes one
method. Methods call each other in the same shape as the grammar,
which is what makes this "recursive descent."

We keep a `pos` cursor into the token list and two helper primitives:
  - peek()    : look at current token without consuming it
  - advance() : consume current token and move cursor forward
  - expect()  : advance, but raise an error if the token isn't the kind we need

Everything else is built from those three.
"""

from lexer import tokenize
from ast_nodes import Num, Ident, BinOp, VarDecl, Assign, If, For, Return, Program


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- token cursor primitives ----------

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind):
        tok = self.peek()
        if tok.kind != kind:
            raise ParseError(f"line {tok.line}: expected {kind}, got {tok.kind} ({tok.value!r})")
        return self.advance()

    # ---------- grammar rules, top to bottom ----------

    def parse_program(self):
        # 'int' 'main' '(' ')' '{' statement* '}'
        self.expect("INT")
        self.expect("IDENT")   # 'main' - we don't validate the name, single-function subset
        self.expect("LPAREN")
        self.expect("RPAREN")
        self.expect("LBRACE")

        body = []
        while self.peek().kind != "RBRACE":
            body.append(self.parse_statement())

        self.expect("RBRACE")
        return Program(body=body)

    def parse_statement(self):
        tok = self.peek()
        if tok.kind == "INT":
            return self.parse_decl()
        elif tok.kind == "IF":
            return self.parse_if()
        elif tok.kind == "FOR":
            return self.parse_for()
        elif tok.kind == "RETURN":
            return self.parse_return()
        elif tok.kind == "IDENT":
            return self.parse_assign()
        else:
            raise ParseError(f"line {tok.line}: unexpected token {tok.kind}")

    def parse_decl(self):
        # 'int' IDENT ('=' expr)? ';'
        line = self.peek().line
        self.expect("INT")
        name_tok = self.expect("IDENT")

        init = None
        if self.peek().kind == "ASSIGN":
            self.advance()
            init = self.parse_expr()

        self.expect("SEMI")
        return VarDecl(name=name_tok.value, init=init, line=line)

    def parse_assign(self, consume_semi=True):
        # IDENT '=' expr (';')
        line = self.peek().line
        name_tok = self.expect("IDENT")
        self.expect("ASSIGN")
        value = self.parse_expr()
        if consume_semi:
            self.expect("SEMI")
        return Assign(name=name_tok.value, value=value, line=line)

    def parse_if(self):
        # 'if' '(' condition ')' '{' statement* '}'
        line = self.peek().line
        self.expect("IF")
        self.expect("LPAREN")
        condition = self.parse_condition()
        self.expect("RPAREN")
        self.expect("LBRACE")

        body = []
        while self.peek().kind != "RBRACE":
            body.append(self.parse_statement())
        self.expect("RBRACE")

        return If(condition=condition, body=body, line=line)

    def parse_for(self):
        # 'for' '(' (decl|assign) ';' condition ';' assign_no_semi ')' '{' statement* '}'
        line = self.peek().line
        self.expect("FOR")
        self.expect("LPAREN")

        # init clause: could be 'int i = 0' (decl) or 'i = 0' (assign) - either way ends in ';'
        if self.peek().kind == "INT":
            init = self.parse_decl()   # parse_decl already consumes trailing ';'
        else:
            init = self.parse_assign()  # consumes trailing ';'

        condition = self.parse_condition()
        self.expect("SEMI")

        step = self.parse_assign(consume_semi=False)  # no ';' before the ')'
        self.expect("RPAREN")

        self.expect("LBRACE")
        body = []
        while self.peek().kind != "RBRACE":
            body.append(self.parse_statement())
        self.expect("RBRACE")

        return For(init=init, condition=condition, step=step, body=body, line=line)

    def parse_return(self):
        line = self.peek().line
        self.expect("RETURN")
        value = self.parse_expr()
        self.expect("SEMI")
        return Return(value=value, line=line)

    def parse_condition(self):
        # expr ('<' | '>' | '==') expr
        line = self.peek().line
        left = self.parse_expr()
        op_tok = self.advance()  # LT, GT, or EQ
        if op_tok.kind not in ("LT", "GT", "EQ"):
            raise ParseError(f"line {op_tok.line}: expected comparison operator, got {op_tok.kind}")
        right = self.parse_expr()
        return BinOp(op=op_tok.value, left=left, right=right, line=line)

    # ---------- expression rules (this is where precedence comes from) ----------

    def parse_expr(self):
        # term (('+' | '-') term)*
        line = self.peek().line
        node = self.parse_term()
        while self.peek().kind in ("PLUS", "MINUS"):
            op_tok = self.advance()
            right = self.parse_term()
            node = BinOp(op=op_tok.value, left=node, right=right, line=line)
        return node

    def parse_term(self):
        # factor (('*' | '/') factor)*
        line = self.peek().line
        node = self.parse_factor()
        while self.peek().kind in ("STAR", "SLASH"):
            op_tok = self.advance()
            right = self.parse_factor()
            node = BinOp(op=op_tok.value, left=node, right=right, line=line)
        return node

    def parse_factor(self):
        # NUMBER | IDENT | '(' expr ')'
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.advance()
            return Num(value=int(tok.value), line=tok.line)
        elif tok.kind == "IDENT":
            self.advance()
            return Ident(name=tok.value, line=tok.line)
        elif tok.kind == "LPAREN":
            self.advance()
            node = self.parse_expr()
            self.expect("RPAREN")
            return node
        else:
            raise ParseError(f"line {tok.line}: unexpected token {tok.kind} in expression")


def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()


if __name__ == "__main__":
    with open("../test_input.c") as f:
        src = f.read()

    ast = parse(src)
    from pprint import pprint
    pprint(ast)