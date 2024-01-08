import vera

from utils import is_source_file, is_header_file, ASSIGN_TOKENS, VALUE_MODIFIER_TOKENS, INCREMENT_DECREMENT_TOKENS, \
    Token
from utils.functions import for_each_function_with_statements

def _report(token: Token) -> None:
    vera.report(
        token.file,
        token.line,
        'MAJOR:C-C2'
    )


def get_statements_using_ternary_operator(statements: list[list[Token]]) -> list[list[Token]]:
    return list(filter(lambda s: any(t.type == 'question_mark' for t in s), statements))

def are_branches_identical(first_branch: list[Token], second_branch: list[Token]) -> bool:
    tokens_to_ignore = {'leftparen', 'rightparen', 'leftbrace', 'rightbrace'}
    first_branch_content = ''.join(t.value for t in first_branch if t.type not in tokens_to_ignore)
    second_branch_content = ''.join(t.value for t in second_branch if t.type not in tokens_to_ignore)
    return first_branch_content == second_branch_content

def check_for_identical_branches(
        statement: list[Token],
        first_ternary_operator_index: int | None,
        first_colon_index: int | None
) -> None:
    if first_ternary_operator_index is not None and first_colon_index is not None:
        first_branch = statement[first_ternary_operator_index + 1:first_colon_index]
        second_branch = statement[first_colon_index + 1:]
        if second_branch[-1].type == 'semicolon':
            second_branch = second_branch[:-1]
        if are_branches_identical(first_branch, second_branch):
            _report(statement[first_ternary_operator_index])


def _is_possible_function_call(statement: list[Token], i: int) -> bool:
    return statement[i].type == 'identifier' and i + 1 < len(statement) and statement[i + 1].type == 'leftparen'


def _check_ternary_operator_statement(statement: list[Token]) -> None:
    first_ternary_operator_encountered = False
    is_value_used = False
    first_ternary_operator_index = None
    first_colon_index = None
    parentheses_depth = 0
    possible_function_call = False
    for i, token in enumerate(statement):
        if ((token.type == 'semicolon' and i != len(statement) - 1)
                or (token.type in INCREMENT_DECREMENT_TOKENS and is_value_used)):
            # Several sub-statements embedded in a single statement
            # or increment/decrement in ternary operator
            _report(token)
        elif first_ternary_operator_encountered:
            # Nested ternary operator or assignation in operator
            if token.type == 'question_mark' or token.type in VALUE_MODIFIER_TOKENS:
                _report(token)
            elif token.type == 'colon':
                first_colon_index = i
        else:
            # First ternary not yet encountered
            if token.type == 'question_mark':
                first_ternary_operator_encountered = True
                first_ternary_operator_index = i
                if possible_function_call and parentheses_depth > 0:
                    is_value_used = True
                # Ternary operator without assignation or return
                if not is_value_used:
                    _report(token)
            elif token.type in {*ASSIGN_TOKENS, 'return'}:
                is_value_used = True
                if token.type in ASSIGN_TOKENS and parentheses_depth > 0:
                    # Assignation in ternary operator condition
                    _report(token)
            possible_function_call = possible_function_call or _is_possible_function_call(statement, i)
            parentheses_depth += token.type == 'leftparen'
            parentheses_depth -= token.type == 'rightparen'
    # Checks for identical branches
    check_for_identical_branches(statement, first_ternary_operator_index, first_colon_index)


def _check_ternary_operator_for_function(statements: list[list[Token]]) -> None:
    for statement in get_statements_using_ternary_operator(statements):
        _check_ternary_operator_statement(statement)



def check_ternary_operator():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue
        for_each_function_with_statements(file, _check_ternary_operator_for_function)


check_ternary_operator()
