import re
from dataclasses import dataclass
from os import path
from sys import stderr

from enum import Enum, auto
from typing import List, Optional, Sequence

import vera
from .cache import cached, cached_filename

LOWER_SNAKECASE_REGEX = re.compile(r'^[a-z](?:_?[a-z0-9]+)*$')
UPPER_SNAKECASE_REGEX = re.compile(r'^[A-Z](?:_?[A-Z0-9]+)*$')

ASSIGN_TOKENS = [
    'assign',
    'plusassign',
    'minusassign',
    'starassign',
    'divideassign',
    'percentassign',
    'xorassign',
    'andassign',
    'shiftleftassign',
    'shiftrightassign',
    'orassign'
]

BINARY_OPERATORS_TOKENS = [
    'plus',
    'minus',
    'star',
    'divide',
    'greater',
    'greaterequal',
    'less',
    'lessequal',
    'equal',
    'notequal',
    'or',
    'andand',
    'and',
    'percent',
    'xor',
    'shiftleft',
    'shiftright',
    'oror',
    'colon',
    'question_mark'
] + ASSIGN_TOKENS

PREPROCESSOR_TOKENS = [
    'pp_define',
    'pp_elif',
    'pp_else',
    'pp_endif',
    'pp_error',
    'pp_hheader',
    'pp_if',
    'pp_ifdef',
    'pp_ifndef',
    'pp_include',
    'pp_line',
    'pp_number',
    'pp_pragma',
    'pp_qheader',
    'pp_undef',
    'pp_warning'
]

UNARY_OPERATORS_TOKENS = [
    'and',
    'plus',
    'minus',
    'not',
    'sizeof',
    'star'
]

INCREMENT_DECREMENT_TOKENS = [
    'plusplus',
    'minusminus'
]

VALUE_MODIFIER_TOKENS = ASSIGN_TOKENS + INCREMENT_DECREMENT_TOKENS

LITERALS_TOKENS = [
    'intlit',
    'stringlit',
    'charlit',
    'floatlit',
    'longintlit'
]

TYPES_TOKENS = [
    'auto',
    'bool',
    'char',
    'comma',
    'const',
    'decimalint',
    'double',
    'enum',
    'extern',
    'float',
    'hexaint',
    'inline',
    'int',
    'long',
    'mutable',
    'octalint',
    'register',
    'short',
    'signed',
    'static',
    'typedef',
    'union',
    'unsigned',
    'virtual',
    'void',
    'volatile',
    'struct'
]

IDENTIFIERS_TOKENS = [
    'identifier',
] + LITERALS_TOKENS

KEYWORDS_TOKENS = [
    'break',
    'default',
    'return',
    'case',
    'continue',
    'default',
    'goto',
    'typeid',
    'typename',
    'struct',
    'if',
    'for',
    'while',
    'do',
    'switch'
]

PARENTHESIS_TOKENS = [
    'leftparen',
    'rightparen'
]

SQUARE_BRACKETS_TOKENS = [
    'leftbracket',
    'rightbracket'
]

BRACE_TOKENS = [
    'leftbrace',
    'rightbrace'
]

CONTROL_STRUCTURE_TOKENS = [
    'if',
    'else',
    'while',
    'do',
    'for',
    'switch'
]

COMMENT_TOKENS = [
    'ccomment',
    'cppcomment'
]

# Tokens that do not influence the semantic of the code
NON_SEMANTIC_TOKENS = [
    'space',
    'space2',
    'newline',
] + COMMENT_TOKENS

STRUCTURE_ACCESS_OPERATORS_TOKENS = [
    'dot',
    'arrow',
    'arrowstar'
]

@dataclass
class Token:
    file: str
    value: str
    line: int
    column: int
    name: str
    type: str
    raw: str


@cached_filename
def is_header_file(file: str) -> bool:
    return file.endswith('.h') and not is_binary(file)


@cached_filename
def is_source_file(file: str) -> bool:
    return file.endswith('.c') and not is_binary(file)


def is_makefile(file: str) -> bool:
    if is_binary(file):
        return False

    return (
        get_extension(file) in ('.mk', '.mak', '.make')
        or any(
            get_filename(file).startswith(makefile_name)
            for makefile_name in ("Makefile", "makefile", "GNUmakefile")
        )
    )


def is_binary(file: str) -> bool:
    return vera.isBinary(file)


def get_extension(file: str) -> str:
    _, extension = path.splitext(file)
    return extension


def get_filename_without_extension(file: str) -> str:
    extension = get_extension(file)
    if extension:
        return path.basename(path.splitext(file)[0])
    return path.basename(file)


@cached_filename
def get_filename(file: str) -> str:
    return path.basename(file)


def is_upper_snakecase(raw: str) -> bool:
    return re.fullmatch(UPPER_SNAKECASE_REGEX, raw) is not None


def is_lower_snakecase(raw: str):
    return re.fullmatch(LOWER_SNAKECASE_REGEX, raw) is not None


def debug_print(s, **kwargs):
    print(s, file=stderr, flush=True, **kwargs)


def __remove_between(lines: List[str], token: Token, begin_token="//", end_token=None) -> None:
    for offset, value in enumerate(token.value.split("\n")):
        line = lines[token.line - 1 + offset]
        has_line_break = line.endswith('\\')

        head = line[:token.column] if offset == 0 else ""
        if (len(line) - (len(head) + len(value))) > 0:
            tail = line[-(len(line) - (len(head) + len(value))):]
        else:
            tail = ""

        if begin_token and end_token and value.startswith(begin_token) and value.endswith(end_token):
            line = head + begin_token + ' ' * (len(value) - (len(begin_token) + len(end_token))) + end_token + tail
        elif begin_token and value.startswith(begin_token):
            line = head + begin_token + ' ' * (len(value) - len(begin_token)) + tail
        elif end_token and value.endswith(end_token):
            line = head + ' ' * (len(value) - len(end_token)) + end_token + tail
        else:
            line = ' ' * len(line)

        if has_line_break:
            line = line[:-1] + '\\'

        lines[token.line - 1 + offset] = line


def __reset_token_value(lines: List[str], token:Token) -> Token:
    value = token.value
    line = lines[token.line - 1][token.column:]
    offset = 0
    while not line.replace('\\', '').replace('\n', '').startswith(value.replace('\\', '').replace('\n', '')) and (token.line - 1 + offset + 1) < len(lines):
        offset += 1
        line = line + '\n' + lines[token.line - 1 + offset]
    diff = len(line.replace('\\', '').replace('\n', '')) - len(value.replace('\\', '').replace('\n', ''))
    if diff > 0:
        line = line[:-diff]
    return Token(
        token.file,
        line,
        token.line,
        token.column,
        token.name,
        token.type,
        token.raw
    )


def _compute_get_lines_cache_key(file: str, replace_comments=False, replace_stringlits=False):
    # Hash key for get_lines: (Hash, bool, bool) which is a valid Dict key
    return hash(file), replace_comments, replace_stringlits


@cached(_compute_get_lines_cache_key)
def get_lines(file: str, replace_comments=False, replace_stringlits=False) -> List[str]:
    lines = vera.getAllLines(file)
    if replace_comments or replace_stringlits:
        lines = [l[:] for l in lines]
    if replace_comments:
        comments = vera.getTokens(file, 1, 0, -1, -1, ['ccomment', 'cppcomment'])
        for comment in comments:
            comment = __reset_token_value(lines, comment)
            if comment.type == 'ccomment':  # /*  */
                __remove_between(lines, comment, '/*', '*/')
            elif comment.type == 'cppcomment':  # //
                __remove_between(lines, comment, '//')

    if replace_stringlits:
        stringlits = vera.getTokens(file, 1, 0, -1, -1, ['stringlit'])
        for stringlit in stringlits:
            stringlit = __reset_token_value(lines, stringlit)
            __remove_between(lines, stringlit, '"', '"')
    return lines


def is_line_empty(line: str):
    # A line only made of spaces is considered empty
    return len(line) == 0 or line.isspace()


def get_index_from_raw(raw: str, line: int, column: int):
    lines = raw.split('\n')
    len_before_current_line = len('\n'.join(lines[:line - 1]))
    len_before_column = lines[line - 1][:column]
    return len_before_current_line + len_before_column


def get_prev_token_index(tokens: List[Token], index: int, types_filters: List[str]):
    for i in range(0, index):
        token = tokens[index - i - 1]
        if token.name in types_filters:
            return index - i - 1
    return -1


def get_next_token_index(tokens: List[Token], index: int, types_filters: List[str]):
    for i in range(index + 1, len(tokens)):
        token = tokens[i]
        if token.name in types_filters:
            return i
    return -1


class StarType(Enum):
    MULTIPLICATION = auto()
    DEREFENCE = auto()
    POINTER = auto()
    LONELY = auto()
    UNCLEAR = auto()


def _parse_star_left_paren(names: List[str], tok_count: int, index: int) -> StarType:
    # lonely ptr, eg : `*(int *(*)[])`
    if names[index + 1] == "rightparen":
        return StarType.LONELY

    if names[index + 1] == "identifier":
        # type ptr or dereference
        while index < tok_count and names[index] != "rightparen":
            index += 1

        if index == tok_count:
            return StarType.UNCLEAR

        # - Dereference: not followed by a leftparen or leftbracket
        if index + 1 < len(names) and names[index + 1] not in {"leftparen", "leftbracket"}:
            return StarType.DEREFENCE

        # - Function: ptr (*f)(...)
        # - Type:  int (*arr)[3]
        return StarType.POINTER

    return StarType.UNCLEAR


def _parse_star_left_token(names: List[str], tok_count: int, index: int) -> Optional[StarType]:

    if names[index - 1] == "leftparen":
        return _parse_star_left_paren(names, tok_count, index)

    if names[index - 1] == "rightparen":
        return StarType.MULTIPLICATION

    if names[index - 1] == "star":
        has_ident = all(name not in TYPES_TOKENS for name in names[:index])
        return StarType.DEREFENCE if has_ident else StarType.POINTER

    if names[index - 1] == "assign":
        return StarType.DEREFENCE

    return None


def get_star_token_type(tokens: Sequence["vera.Token"], index: int) -> StarType:
    token = tokens[index]

    code_tokens = [t for t in tokens if t.name != "space"]
    index = find_token_index(code_tokens, token)

    names = [t.name for t in code_tokens]
    tok_count = len(names)

    if index in {0, tok_count}:
        return StarType.UNCLEAR

    conclusion = _parse_star_left_token(names, tok_count, index)
    if conclusion is not None:
        return conclusion

    # If the line contains very few tokens, it can be unclear
    # whether the statement is a multiplication or a pointer declaration.

    # However, it is way more likely to be a pointer declaration as
    # a unassigned multiplication would be useless to the program.

    # Eg: `sfEvent *event` vs `a * b`
    # We will prioterize pointer declaration for known types
    if (
        names[index + 1] in {"semicolon", "assign"}
        or names[index - 1] in TYPES_TOKENS
        or code_tokens[index - 1].value.endswith('_t')
    ):
        return StarType.POINTER

    return StarType.UNCLEAR


def find_token_index(tokens, target) -> int:
    for i, token in enumerate(tokens):
        if token.column == target.column and token.line == target.line:
            return i

    return -1


def filter_out_non_semantic_tokens(tokens: List[Token]) -> List[Token]:
    return list(filter(lambda t: t.name not in NON_SEMANTIC_TOKENS, tokens))
