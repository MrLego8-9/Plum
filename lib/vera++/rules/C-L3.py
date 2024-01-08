import re
from typing import List

import vera
from utils import (
    PARENTHESIS_TOKENS,
    KEYWORDS_TOKENS,
    BINARY_OPERATORS_TOKENS,
    IDENTIFIERS_TOKENS,
    UNARY_OPERATORS_TOKENS,
    TYPES_TOKENS,
    SQUARE_BRACKETS_TOKENS,
    COMMENT_TOKENS,

    Token,
    is_source_file,
    is_header_file,
    get_prev_token_index, BRACE_TOKENS
)

SEPARATOR_TOKENS = [
    'comma',
    'semicolon'
]

SPACES_TOKENS = [
    'space',
    'newline'
]

SPACE_RELATED_TOKENS = (
        BINARY_OPERATORS_TOKENS
        + UNARY_OPERATORS_TOKENS
        + SPACES_TOKENS
        + IDENTIFIERS_TOKENS
        + TYPES_TOKENS
        + PARENTHESIS_TOKENS
        + SEPARATOR_TOKENS
        + SQUARE_BRACKETS_TOKENS
        + BRACE_TOKENS
        + KEYWORDS_TOKENS
        + ['pp_define']
        + ['and']
        + ['sizeof']
)

KEYWORDS_NEEDS_SPACE = (
    'if',
    'switch',
    'case',
    'for',
    'do',
    'while',
    'return',
    'comma',
    'struct',
)


def __report(token: Token) -> None:
    vera.report(token.file, token.line, "MINOR:C-L3")


def _is_invalid_space_legacy(tokens: List[Token], i: int):
    # If there is a new line or a single space the space is always valid
    if tokens[i].name == 'newline' or tokens[i].value == ' ':
        return False
    # If there is multiple spaces but these spaces was preceded by a new line this is valid
    if i > 0 and tokens[i].name == 'space' and tokens[i - 1].name == 'newline':
        return False
    # If there is multiple spaces but these spaces are followed by a new line or a comment this is valid
    if i + 1 < len(tokens) and tokens[i].name == 'space' and tokens[i + 1].name in ('newline', *COMMENT_TOKENS):
        return False
    # Elsewhere the space is invalid
    return True


def _is_invalid_space(token: Token) -> bool:
    return token.name == 'space' and token.value != ' '


def _check_binary_operator(token, i, tokens, prev_token_indeces):
    prev_case_token_index, prev_separator_token_index = prev_token_indeces

    # Check for space before
    if i == 0:
        return
    # Special case for the Elvis operator
    if token.name == 'colon' and tokens[i - 1].name == 'question_mark':
        return
    if (
            prev_case_token_index < prev_separator_token_index
            or prev_case_token_index < 0
    ) and _is_invalid_space_legacy(tokens, i - 1):
        __report(token)
        return
    # Check for space after
    if i + 1 < len(tokens):
        # Special case for the Elvis operator
        if token.name == 'question_mark' and tokens[i + 1].name == 'colon':
            return
        if (
                prev_case_token_index < prev_separator_token_index
                or prev_case_token_index < 0
        ) and _is_invalid_space_legacy(tokens, i + 1):
            __report(token)


def _check_ampersand(token, i, tokens):
    """
    Reports if there is a space after an ampersand and not before
    """
    if token.name != 'and':
        return

    if i in (1, len(tokens) - 1):
        return

    if tokens[i - 1].name != 'space' and tokens[i + 1].name == 'space':
        __report(token)


def check_space_around_operators(file):
    tokens = vera.getTokens(file, 1, 0, -1, -1, SPACE_RELATED_TOKENS)
    target_operators = UNARY_OPERATORS_TOKENS + BINARY_OPERATORS_TOKENS

    for i, token in enumerate(tokens):
        _check_ampersand(token, i, tokens)

        if token.name not in target_operators:
            continue

        prev_case_token_index = get_prev_token_index(tokens, i, ['case', 'default'])
        prev_separator_token_index = get_prev_token_index(tokens, i, ['comma', 'semicolon', 'leftbrace'])

        if token.name not in UNARY_OPERATORS_TOKENS:
            _check_binary_operator(
                token, i, tokens,
                (prev_case_token_index, prev_separator_token_index)
            )
            continue
        if i in (0, len(tokens) - 1):
            continue

        allowed_previous_tokens = ['not', 'and']
        operator_separators_tokens = (
                SPACES_TOKENS
                + PARENTHESIS_TOKENS
                + SQUARE_BRACKETS_TOKENS
                + BRACE_TOKENS
                + [token.name]
        )

        if (
                tokens[i - 1].name not in allowed_previous_tokens
                and tokens[i - 1].name not in operator_separators_tokens
                and tokens[i + 1].name not in operator_separators_tokens
        ):
            __report(token)


def _check_for_return_case(token, i, tokens):
    # "return" keyword is an exception,
    # where it needs to be immediately followed by either a space
    #  and something else than a semicolon,
    #  or immediately by a semicolon without a space in between
    if tokens[i + 1].name == 'semicolon':
        return
    if tokens[i + 1].name not in SPACES_TOKENS:
        __report(token)
    elif (
            i + 2 >= len(tokens)
            or tokens[i + 2].name == 'semicolon'
            or _is_invalid_space_legacy(tokens, i + 1)
    ):
        __report(token)


def check_space_after_keywords_and_commas(file):
    tokens = vera.getTokens(file, 1, 0, -1, -1, [])
    target_tokens = KEYWORDS_TOKENS + ['comma']

    for i, token in enumerate(tokens):
        if token.name not in target_tokens:
            continue

        if (i + 1) >= len(tokens):
            continue

        if token.name == 'return':
            _check_for_return_case(token, i, tokens)
        # If the token needs to have a space,
        # and that there is not space after it, it is an error
        elif (
                token.name in KEYWORDS_NEEDS_SPACE
                and _is_invalid_space_legacy(tokens, i + 1)
        ):
            __report(token)
        # If the token does not need to have a space,
        # and that there is a space after it, it is an error
        elif (
                token.name not in KEYWORDS_NEEDS_SPACE
                and tokens[i + 1].name in SPACES_TOKENS
        ):
            __report(token)


def _trim_line_tokens(line_tokens) -> List[Token]:
    trimmed_line_tokens = line_tokens
    # Remove leading spaces
    if len(trimmed_line_tokens) >= 1 and trimmed_line_tokens[0].name == 'space':
        trimmed_line_tokens = trimmed_line_tokens[1:]
    # Remove newline
    if len(trimmed_line_tokens) >= 1 and trimmed_line_tokens[-1].name == 'newline':
        trimmed_line_tokens = trimmed_line_tokens[:-1]
    # Remove trailing spaces
    if len(trimmed_line_tokens) >= 1 and trimmed_line_tokens[-1].name == 'space':
        trimmed_line_tokens = trimmed_line_tokens[:-1]
    # Remove trailing comments
    if len(trimmed_line_tokens) >= 1 and trimmed_line_tokens[-1].name in COMMENT_TOKENS:
        trimmed_line_tokens = trimmed_line_tokens[:-1]
        # Re-launch the function to remove new trailing spaces
        trimmed_line_tokens = _trim_line_tokens(trimmed_line_tokens)
    return trimmed_line_tokens


# The following token pairs must always be separated by a space
MANDATORY_SPACE_NEIGHBORS: set[tuple[str, str]] = {
    ('identifier', 'leftbrace'),
    ('semicolon', 'identifier'),
}

# The following tokens must always be followed by a space
MANDATORY_SPACE_PREDECESSORS: set[str] = {
    'pp_include',
    'else',
}

# The following tokens must always be preceded by a space
MANDATORY_SPACE_SUCCESSORS: set[str] = {
    'else',
}

# The following token pairs must never be separated by a space
FORBIDDEN_SPACE_NEIGHBORS: set[tuple[str, str]] = {
    ('identifier', 'leftparen'),
    ('sizeof', 'leftparen'),
    ('rightparen', 'semicolon'),
}

# The following tokens must never be followed by a space
FORBIDDEN_SPACE_PREDECESSORS = {
    'leftparen',
    'leftbracket',
    'arrow',
    'not',
}

# The following tokens must never be preceded by a space
FORBIDDEN_SPACE_SUCCESSORS = {
    'leftbracket',
    'rightparen',
    'rightbracket',
    'comma',
    'semicolon',
    'arrow',
}


def _is_space_missing(token_name: str | None, next_token_name: str | None) -> bool:
    if token_name is None or next_token_name is None:
        return False
    if (token_name, next_token_name) in MANDATORY_SPACE_NEIGHBORS:
        return True
    if token_name != 'space' and next_token_name in MANDATORY_SPACE_SUCCESSORS:
        return True
    if next_token_name != 'space' and token_name in MANDATORY_SPACE_PREDECESSORS:
        return True
    return False


def _is_unwanted_space(prev_token_name: str | None, token_name: str, next_token_name: str | None) -> bool:
    if token_name != 'space':
        return False
    return (
            (prev_token_name, next_token_name) in FORBIDDEN_SPACE_NEIGHBORS
            or prev_token_name in FORBIDDEN_SPACE_PREDECESSORS
            or next_token_name in FORBIDDEN_SPACE_SUCCESSORS
    )


def _is_invalid_include_spacing(token: Token) -> bool:
    return (
            token.name in ('pp_qheader', 'pp_hheader')
            and token.value.startswith('#include')
            and re.fullmatch(r'#include( [^ ].*)?$', token.value) is None
    )


def _get_neigbors_tokens_names(i, line_tokens):
    previous_token_name = line_tokens[i - 1].name if i > 0 else None
    next_token_name = line_tokens[i + 1].name if i + 1 < len(line_tokens) else None
    return previous_token_name, next_token_name


def _check_unwanted_spaces(token, i, line_tokens):
    if line_tokens[0].name == 'pp_define':
        return

    if _is_invalid_space(token):
        __report(token)
        return

    if _is_invalid_include_spacing(token):
        __report(token)
        return

    (previous_token_name, next_token_name) = _get_neigbors_tokens_names(i, line_tokens)

    if (
            _is_space_missing(token.name, next_token_name)
            or _is_unwanted_space(previous_token_name, token.name, next_token_name)
    ):
        __report(token)


def _get_tokens_grouped_by_line(file):
    tokens = vera.getTokens(file, 1, 0, -1, -1, [])
    lines_tokens: List[List[Token]] = []
    line = 0
    for token in tokens:
        if token.line != line:
            lines_tokens.append([])
            line = token.line
        lines_tokens[-1].append(token)
    lines_tokens = [_trim_line_tokens(lt) for lt in lines_tokens]
    lines_tokens = [lt for lt in lines_tokens if lt]
    return lines_tokens


def check_spaces_line_by_line(file):
    lines_tokens: List[List[Token]] = _get_tokens_grouped_by_line(file)

    for line_tokens in lines_tokens:
        for i, token in enumerate(line_tokens):
            _check_unwanted_spaces(token, i, line_tokens)


def check_spaces():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        check_space_after_keywords_and_commas(file)
        check_space_around_operators(file)
        check_spaces_line_by_line(file)


check_spaces()
