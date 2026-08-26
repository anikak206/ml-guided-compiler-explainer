"""
Phase 2a: Lexer
----------------
Turns raw C source text into a flat list of Tokens.
A Token is just: (kind, value, line_number)

We track line_number on every token because that's how we'll later tag
IR instructions back to source lines (needed for the LLM explanation phase).
"""

import re # provides tools to work with regular expressions
from dataclasses import dataclass # creates clean, readable data containers

@dataclass
class Token:
    kind: str    
    value: str   
    line: int    

# few basic keywords
KEYWORDS = {"int", "if", "for", "return"}

TOKEN_SPEC = [
    ("NUMBER",   r"\d+"),
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),
    ("EQ",       r"=="),
    ("ASSIGN",   r"="),
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("STAR",     r"\*"),
    ("SLASH",    r"/"),
    ("LT",       r"<"),
    ("GT",       r">"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("SEMI",     r";"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t]+"),
    ("COMMENT",  r"//[^\n]*"),
]

MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
) # a master regex pattern consisting of all the possible token patterns joined with "|"

def tokenize(source: str) -> list[Token]:
    tokens = [] # initially the tokens are zero
    line = 1 # keeps track of lines in source code
    for match in MASTER_PATTERN.finditer(source): # match = every token match that has occured between source code and the regex pattern
        kind = match.lastgroup # tells us which named regex group matched. For eg. for int kind = IDENT
        value = match.group() # the value that was matched

        if kind == "NEWLINE": # increment the line
            line += 1
            continue
        if kind in ("SKIP", "COMMENT"): # SKIP represents spaces while COMMENT represents comments
            continue

        if kind == "IDENT" and value in KEYWORDS: # few identifiers are actually tokens
            kind = value.upper()  

        tokens.append(Token(kind, value, line)) # add the token object to the list

    tokens.append(Token("EOF", "", line)) # represents end of the list or file
    return tokens


if __name__ == "__main__": # run the following code only when the Python file is executed directly
    # Quick manual test: tokenize our test file and print every token
    with open("test/sample_inputs/sample_input_1.c") as f: # "with" closes the file after the execution of the block
        src = f.read()

    for tok in tokenize(src):
        print(f"line {tok.line:>2}  {tok.kind:<8} {tok.value!r}") # prints each token