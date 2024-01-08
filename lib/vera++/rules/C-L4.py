import re
from typing import List

import vera
from utils import is_source_file, is_header_file, Token, get_lines, CONTROL_STRUCTURE_TOKENS
from utils.functions import get_functions, for_each_function_with_statements
from utils.functions.function import Function


def __report(token: Token) -> None:
    vera.report(token.file, token.line, "MINOR:C-L4")

def get_function_start_at_token(functions: List[Function], token: Token) -> Function | None:
    for function in functions:
        if function.body and function.body.line_start == token.line and function.body.column_start == token.column:
            return function
    return None


def _is_left_brace_misplaced(statement: list[Token], i: int, statements: list[list[Token]]) -> bool:
    if statement[-1].name != 'leftbrace':
        return False
    if i + 1 < len(statements) and statement[-1].line == statements[i + 1][0].line:
        # The left brace is followed by a token on the same line
        return True
    if len(statement) > 1 and statement[-1].line != statement[-2].line:
        # The left brace is not preceded by a token on the same line
        return True
    return False



def _is_right_brace_misplaced(
        statement: list[Token],
        i: int,
        statements: list[list[Token]],
        is_in_do: bool
) -> bool:
    if statement[0].name != 'rightbrace':
        return False
    if i - 1 >= 0 and statement[0].line == statements[i - 1][-1].line:
        # The right brace is preceded by a token on the same line
        return True
    if i + 1 < len(statements):
        if statements[i + 1][0].name == 'else' or (is_in_do and statements[i + 1][0].name == 'while'):
            return statement[0].line != statements[i + 1][0].line
        # The right brace is followed by a token on the same line (except else)
        return statement[0].line == statements[i + 1][0].line
    return False


def _check_braces_placement_in_function(statements: list[list[Token]]) -> None:
    control_structure_nesting = []
    for i, statement in enumerate(statements):
        if statement[0].name in CONTROL_STRUCTURE_TOKENS and statement[-1].name == 'leftbrace':
            control_structure_nesting.append(statement[0].name)
        if (_is_left_brace_misplaced(statement, i, statements)
                or _is_right_brace_misplaced(
                    statement,
                    i,
                    statements,
                    len(control_structure_nesting) > 0 and control_structure_nesting[-1] == 'do'
                )
        ):
            __report(statement[-1])
        if statement[-1].name == 'rightbrace':
            if len(control_structure_nesting) > 0:
                control_structure_nesting.pop()


def _is_token_part_of_function_body(token: Token, functions: list[Function]) -> bool:
    for function in functions:
        if function.body is None:
            continue
        if function.body.line_start < token.line < function.body.line_end:
            return True
        if function.body.line_start == token.line and function.body.line_end == token.line:
            return function.body.column_start < token.column < function.body.column_end
        if function.body.line_start == token.line and function.body.column_start < token.column:
            return True
        if function.body.line_end == token.line and function.body.column_end > token.column:
            return True
    return False

# pylint:disable=too-many-branches
# pylint:disable=too-many-locals
# pylint:disable=too-many-statements
def check_curly_brackets_placement():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        for_each_function_with_statements(file, _check_braces_placement_in_function)

        tokens_filter = [
            'leftbrace',
            'rightbrace',
            "case",
            "do",
            "else",
            "for",
            "if",
            "typedef",
            "switch",
            "while",
            "struct",
            "leftparen",
            "rightparen",
            "enum",
            "assign",
            "union",
            "identifier",
            "semicolon"
        ]
        lines = get_lines(file, True, True)
        tokens = vera.getTokens(file, 1, 0, -1, -1, tokens_filter)
        tokens_count = len(tokens)
        enum_braces_count = []
        union_braces_count = []
        assign_braces_count = []
        struct_braces_count = []
        typedef_struct_braces_count = []
        functions = get_functions(file)
        skipping_level_increase_token = None
        skipping_level_decrease_token = None
        skipping_checks = False
        skipping_level = 0

        for i, token in enumerate(tokens):
            if _is_token_part_of_function_body(token, functions):
                continue
            token_line_content = vera.getLine(file, token.line)

            if not skipping_checks:
                if token.name == 'leftparen':
                    skipping_level = 1
                    skipping_checks = True
                    skipping_level_increase_token = 'leftparen'
                    skipping_level_decrease_token = 'rightparen'
                    continue
                if i > 0 and token.name == 'leftbrace' and tokens[i - 1].name == 'assign':
                    skipping_level = 1
                    skipping_checks = True
                    skipping_level_increase_token = 'leftbrace'
                    skipping_level_decrease_token = 'rightbrace'
                    continue

            if skipping_checks:
                if token.name == skipping_level_increase_token:
                    skipping_level += 1
                elif token.name == skipping_level_decrease_token:
                    skipping_level -= 1
                if skipping_level == 0:
                    skipping_checks = False
                continue

            if token.name == 'enum':
                enum_braces_count.append(0)
            elif token.name == 'assign':
                assign_braces_count.append(0)
            elif token.name == 'union':
                union_braces_count.append(0)
            elif token.name == 'typedef' and i + 1 < tokens_count and tokens[i + 1].name == 'struct':
                typedef_struct_braces_count.append(0)
            elif token.name == 'struct':
                struct_braces_count.append(0)

            elif token.name == 'leftbrace':
                # Count the braces of a typedef struct or enum in order to detect the end of the bloc
                if len(enum_braces_count) > 0:
                    enum_braces_count[-1] += 1
                if len(assign_braces_count) > 0:
                    assign_braces_count[-1] += 1
                if len(union_braces_count) > 0:
                    union_braces_count[-1] += 1
                if len(typedef_struct_braces_count) > 0:
                    typedef_struct_braces_count[-1] += 1
                if len(struct_braces_count) > 0:
                    struct_braces_count[-1] += 1

                func = get_function_start_at_token(functions, token)
                if func is not None and len(lines[token.line - 1]) > 1:  # handling function specific case
                    __report(token)
                elif func is None and i > 0 and tokens[i - 1].line != token.line:
                    __report(token)
                elif i < len(tokens) - 1 and tokens[i + 1].line == token.line: # handling content after left brace
                    __report(token)

            elif token.name == 'rightbrace':
                # Count the braces of a typedef struct or enum in order to detect the end of the bloc
                if len(enum_braces_count) > 0:
                    enum_braces_count[-1] -= 1
                if len(assign_braces_count) > 0:
                    assign_braces_count[-1] -= 1
                if len(union_braces_count) > 0:
                    union_braces_count[-1] -= 1
                if len(typedef_struct_braces_count) > 0:
                    typedef_struct_braces_count[-1] -= 1
                if len(struct_braces_count) > 0:
                    struct_braces_count[-1] -= 1

                # True when it's the end of the enum bloc
                if len(enum_braces_count) > 0 and enum_braces_count[-1] == 0:
                    enum_braces_count.pop()
                    continue

                # True when it's the end of the assign bloc
                if len(assign_braces_count) > 0 and assign_braces_count[-1] == 0:
                    assign_braces_count.pop()
                    continue

                # True when it's the end of the union bloc
                if len(union_braces_count) > 0 and union_braces_count[-1] == 0:
                    union_braces_count.pop()
                    continue

                # True when it's the end of the typedef struct bloc
                if len(typedef_struct_braces_count) > 0 and typedef_struct_braces_count[-1] == 0:
                    typedef_struct_braces_count.pop()
                    continue

                # True when it's the end of the struct bloc
                if len(struct_braces_count) > 0 and struct_braces_count[-1] == 0:
                    struct_braces_count.pop()
                    continue

                if i + 1 < tokens_count and tokens[i + 1].name == 'else':
                    continue
                line = token_line_content.replace(' ', '').replace('\t', '')
                is_valid = re.match("}[ \t]*;?(//.*|/\\*.*)?[ \t]*$", line)
                if not is_valid:
                    __report(token)
            elif token.name == 'else':
                # A righbrace preceding an else must be on the same line
                if i >= 1 and tokens[i - 1].name == 'rightbrace' and tokens[i - 1].line != token.line:
                    __report(token)
                # Check if there is a valid token after the else on the same line
                if (
                        i + 1 >= tokens_count or
                        (tokens[i + 1].name not in ['if', 'leftbrace'] and tokens[i + 1].line == token.line)
                ):
                    __report(token)

            elif token.name == 'if' and i >= 1 and tokens[i - 1].name == 'else':
                if token.line != tokens[i - 1].line:
                    __report(token)



check_curly_brackets_placement()
