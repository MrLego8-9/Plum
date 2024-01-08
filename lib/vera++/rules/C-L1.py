import vera

from utils import is_source_file, is_header_file, CONTROL_STRUCTURE_TOKENS, ASSIGN_TOKENS, Token, \
    INCREMENT_DECREMENT_TOKENS
from utils.functions import for_each_function_with_statements, skip_interval


def __report(token: Token):
    vera.report(token.file, token.line, 'MAJOR:C-L1')


CLOSING_LINE_AUTHORIZED_TOKENS = {
    'if': 'else',
    'do': 'while',
    'else': 'else'
}

VARIABLE_MODIFICATION_TOKENS = [
    *ASSIGN_TOKENS,
    *INCREMENT_DECREMENT_TOKENS
]


def _has_comma_at_root_level(statement: list[Token]) -> bool:
    root_level = 0
    i = 0
    while i < len(statement) and statement[i].name == 'leftparen':
        root_level += 1
        i += 1
    parentheses_depth = 0
    for token in statement[i:]:
        if token.name == 'leftparen':
            parentheses_depth += 1
        elif token.name == 'rightparen':
            parentheses_depth -= 1
        elif token.name == 'comma' and parentheses_depth <= root_level:
            return True
    return False


def _get_for_prototype_parts(statement: list[Token]) -> list[list[Token]]:
    parentheses_depth = 0
    part_start = None
    parts = []
    for i, token in enumerate(statement):
        if token.name == 'leftparen':
            parentheses_depth += 1
            if parentheses_depth == 1:
                part_start = i + 1
        elif token.name == 'rightparen':
            parentheses_depth -= 1
            if parentheses_depth == 0:
                if part_start is not None and part_start < i:
                    parts.append(statement[part_start:i])
                break
        elif token.name == 'semicolon' and parentheses_depth == 1:
            if part_start is not None and part_start < i:
                parts.append(statement[part_start:i])
            part_start = i + 1
    return parts


def _is_structure_initialization(part_after_assign: list[Token]) -> bool:
    if len(part_after_assign) < 3:
        return False
    if part_after_assign[0].name == 'leftbrace':
        return True
    if part_after_assign[0].name == 'leftparen':
        after_paren, _ = skip_interval(part_after_assign, 0, 'leftparen', 'rightparen')
        return after_paren + 1 < len(part_after_assign) and part_after_assign[after_paren + 1].name == 'leftbrace'
    return False

def _is_chained_assignment(statement: list[Token]) -> bool:
    if statement[0].name == 'return':
        # return statements are checked by a different function
        return False
    if statement[0].name == 'for':
        for_prototype_parts = _get_for_prototype_parts(statement)
        return any(_is_chained_assignment(part) or _has_comma_at_root_level(part) for part in for_prototype_parts)
    assign_found = False
    for i, token in enumerate(statement):
        if token.name in VARIABLE_MODIFICATION_TOKENS:
            if assign_found:
                return True
            if i + 1 < len(statement) and _is_structure_initialization(statement[i + 1:]):
                # We encountered a structure initialization, as such we stop looking for assign tokens
                # since the next one will be the one of the structure initialization.
                return False
            assign_found = True
    return False


def _is_assigning_in_control_structure_prototype(statement: list[Token]) -> bool:
    return (statement[0].name in CONTROL_STRUCTURE_TOKENS
            and statement[0].name != 'for'
            and any(True for token in statement if token.name in VARIABLE_MODIFICATION_TOKENS))


def _are_two_statements_on_the_same_line(statements: list[list[Token]], i: int,
                                         right_brace_line_authorized_tokens: list[str]) -> bool:
    return (i > 0 and statements[i][0].line == statements[i - 1][-1].line
            and not (statements[i - 1][0].name == 'rightbrace'
                     and len(right_brace_line_authorized_tokens) > 0
                     and statements[i][0].name == right_brace_line_authorized_tokens[-1]))


def _is_assigning_in_return_statement(statement: list[Token]) -> bool:
    return (statement[0].name == 'return'
            and not _is_structure_initialization(statement[1:])
            and any(True for token in statement if token.name in VARIABLE_MODIFICATION_TOKENS))


def _check_function_statements(statements: list[list[Token]]):
    brace_depth = 0
    right_brace_line_authorized_tokens = []
    for i, statement in enumerate(statements):
        if (_are_two_statements_on_the_same_line(statements, i, right_brace_line_authorized_tokens)
                or _is_assigning_in_control_structure_prototype(statement)
                or _is_chained_assignment(statement)
                or _is_assigning_in_return_statement(statement)):
            # There is a chained assignment
            __report(statement[0])

        if statements[i - 1][0].name == 'rightbrace':
            if len(right_brace_line_authorized_tokens) > 0:
                right_brace_line_authorized_tokens.pop()
        if statement[-1].name == 'leftbrace':
            right_brace_line_authorized_tokens.append(CLOSING_LINE_AUTHORIZED_TOKENS.get(statement[0].name, None))
            brace_depth += 1
        elif statement[0].name == 'rightbrace' and brace_depth > 0:
            brace_depth -= 1


def check_multiple_statements_on_one_line():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        for_each_function_with_statements(file, _check_function_statements)

check_multiple_statements_on_one_line()
