import string

identifier = set(string.ascii_letters) | set(string.digits)
operator = set("+-*/%|&^")
newline = set("\r\n")
ws_nl = set(string.whitespace)
ws = ws_nl - newline

# Counts the number of times the current leading whitespace was dedented
def count_dedents(indents, leading_whitespace) -> int:
    # Note: this could be replaced with a backwards iteration
    if leading_whitespace not in indents:
        raise ValueError(f"Leading whitespace {leading_whitespace!r} not found in indentation stack")
    
    dedents = 0
    for i in range(len(indents) - 1, -1, -1):
        if indents[i] == leading_whitespace:
            break
        dedents += 1
    
    return dedents

class Lexer:
    def __init__(self, input):
        self.input = input
        self.len = len(input)
        self.current = 0
        self.indentation_stack = [""]
        self.tokens = []

    def not_eof(self):
        return self.current < self.len

    def peek(self):
        return self.input[self.current] if self.not_eof() else None
    
    def next(self):
        char = self.peek()
        self.current += 1
        return char

    def skip(self):
        self.current += 1

    def take_while(self, chars: set[str]) -> str:
        start = self.current
        while self.peek() in chars:
            self.current += 1
        return self.input[start:self.current]
    
    def is_single_line_comment_next(self) -> bool:
        if len(self.input) > (self.current + 1):
            return False
        return self.peek() == '/' and self.input[self.current + 1] == '/'

    def is_multi_line_comment_next(self) -> bool:
        if len(self.input) > (self.current + 1):
            return False
        return self.peek() == '/' and self.input[self.current + 1] == '*'

    def take_until(self, chars: set[str]) -> str:
        start = self.current
        while self.peek() not in chars:
            self.current += 1
        return self.input[start:self.current]

    def handle_single_line_comment(self):
        self.take_until(newline)
        self.take_while(newline)
        return self.handle_leading_whitespace()

    def handle_multi_line_comment(self):
        # Take until "*/"
        while not (self.peek() == '*' and self.input[self.current + 1] == '/'):
            self.skip()

        # Skip twice past "*/"
        self.skip()
        self.skip()
        # Note: the end of a multi-line comment is treated as being on the same line, as it does not lex newline characters

    def handle_leading_whitespace(self):
        leading_whitespace = self.take_while(ws)

        # If the line is blank (newline characters or comment only), then discard this token
        if self.peek() in newline:
            self.take_while(newline)
            # Handle the next line's whitespace
            return self.handle_leading_whitespace()
        elif self.is_single_line_comment_next():
            return self.handle_single_line_comment()
        elif self.is_multi_line_comment_next():
            self.handle_multi_line_comment()
            return

        # Get indentation type:
        # Indentation is same: newline
        top_indentation = self.indentation_stack[-1]
        if leading_whitespace == top_indentation:
            self.tokens.append("Newline")

        # Indentation is lesser: dedent
        elif len(leading_whitespace) < len(top_indentation):
            dedents = count_dedents(self.indentation_stack, leading_whitespace)
            for _ in range(dedents):
                self.indentation_stack.pop()
                self.tokens.append("Dedent")

        # Indentation is greater: indent
        elif len(leading_whitespace) > len(top_indentation):
            self.indentation_stack.append(leading_whitespace)
            self.tokens.append("Indent")
        
        # Indentation is wonky: error
        raise RuntimeError("Mismatched indentation!")

    def lex(self):
        while self.not_eof():
            if self.peek() in identifier:
                self.tokens.append(("Word", self.take_while(identifier)))
            elif self.peek() in newline:
                # Ignore blank lines
                while True:
                    self.take_while(newline)
                    self.handle_leading_whitespace()
                    is_eof = not self.not_eof()
                    if self.peek() not in newline or is_eof:
                        if is_eof:
                            self.tokens.pop()
                        break
                    # Undo needless leading whitespace
                    self.tokens.pop()
            elif self.peek() == '\\':
                self.skip()
                # Skip next line's indentation
                self.take_while(ws_nl)
            elif self.peek() in operator:
                # '/' is included in the operators, so its comment sequences need to be handled
                if self.is_single_line_comment_next():
                    self.handle_single_line_comment()
                elif self.is_multi_line_comment_next():
                    self.handle_multi_line_comment()
                else:
                    self.tokens.append(("Operator", self.take_while(operator)))
                    # Skip next line's indentation
                    self.take_while(ws_nl)
            elif self.peek() in ws:
                self.take_while(ws)

file = open("sample.txt")
lexer = Lexer(file.read())
file.close()

lexer.lex()
print("Tokens:")
for token in lexer.tokens:
    print(token)
