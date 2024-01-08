import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Callable, Tuple

import clang.cindex

import vera

from .. import cached_filename, ASSIGN_TOKENS, STRUCTURE_ACCESS_OPERATORS_TOKENS, Token

from .function import Function
from .section import Section
from .utils import remove_attributes, get_column
from .. import CONTROL_STRUCTURE_TOKENS, TYPES_TOKENS, get_lines, filter_out_non_semantic_tokens

RESERVED_KEYWORDS = [
    "break",
    "case",
    "continue",
    "default",
    "do",
    "else",
    "for",
    "goto",
    "if",
    "return",
    "sizeof",
    "switch",
    "typedef",
    "while"
]

FUNCTION_REGEX = re.compile(
    r"(?P<beforeFunction>(^|#.+|(?<=[;}{]))([\n\s*/]*(^|(?<=[\n\s{};]))))"
    r"(?P<func>"
    r"(?P<type>((?!" + r"\W|".join(RESERVED_KEYWORDS) + r"\W)\w+[\w\s\n*,]*|(\w+[\s\t\n*]+)\(\*.*\)\(.*\))[\s\n*]+)"
                                                        r"(?P<name>(?<=[\n\s*])[\w$]+)[\s\n]*\([\n\s]*"
                                                        r"(?P<args>[^;{]*)[\n\s]*\)[\s\n]*"
                                                        r"(?P<functionStartChar>[;{]{1}))"
)


def __get_function_body(file: str, function_start_index: int):
    all_lines = get_lines(file, replace_comments=True)
    raw = '\n'.join(all_lines)
    braces_count = 0
    line_number = raw[:function_start_index].count('\n') + 1
    column_number = get_column(raw, line_number, function_start_index)
    tokens = vera.getTokens(file, line_number, column_number, -1, -1, ['leftbrace', 'rightbrace'])
    end_line_number = -1
    end_column_number = -1

    for token in tokens:
        if token.name == 'leftbrace':
            if braces_count == 0:
                line_number = token.line
                column_number = token.column
            braces_count += 1
        elif token.name == 'rightbrace':
            braces_count -= 1
        if braces_count == 0:
            end_line_number = token.line
            end_column_number = token.column
            break
    function_lines = all_lines[line_number - 1:end_line_number]
    function_lines[0] = function_lines[0][column_number:]
    function_lines[-1] = function_lines[-1][:end_column_number + 1]
    raw = '\n'.join(function_lines)
    return Section(
        line_start=line_number,
        line_end=end_line_number,
        column_start=column_number,
        column_end=end_column_number,
        raw=raw
    )


def __get_arguments_from_string(arguments_string: str):
    arguments_parts_array = arguments_string.split(',')
    argument = ""
    arguments = []

    for argument_part in arguments_parts_array:
        argument += argument_part
        if len(argument.strip()) > 0 and argument.count('(') == argument.count(')'):
            arguments.append(argument)
            argument = ""
    return arguments


def _get_function_from_clang_cursor(cursor: clang.cindex.Cursor, file_contents: str) -> Function:
    has_arguments_list = cursor.type.kind.name == 'FUNCTIONPROTO'
    has_body = False
    body_start = None
    parameters = []
    for c in cursor.get_children():
        if c.kind.name == 'COMPOUND_STMT':
            has_body = True
            body_start = c.extent.start
        elif c.kind.name == 'PARM_DECL':
            parameters.append(file_contents[c.extent.start.offset:c.extent.end.offset])
    body_end: clang.cindex.SourceLocation | None = None
    if has_body:
        body_end = cursor.extent.end
    is_inline = False
    for token in cursor.get_tokens():
        if token.spelling == cursor.spelling:
            break
        if token.spelling == 'inline':
            is_inline = True
            break
    return Function(
        prototype=Section(
            line_start=cursor.extent.start.line,
            line_end=body_start.line if has_body else cursor.extent.end.line,
            column_start=cursor.extent.start.column - 1,
            column_end=(body_start.column if has_body else cursor.extent.end.column) - 1,
            raw=file_contents[cursor.extent.start.offset:body_start.offset] if has_body else
            file_contents[cursor.extent.start.offset:cursor.extent.end.offset]
        ),
        body=Section(
            line_start=body_start.line,
            line_end=body_end.line,
            column_start=body_start.column - 1,
            column_end=body_end.column - 2,
            raw=file_contents[body_start.offset:body_end.offset]
        ) if has_body else None,
        arguments=parameters if has_arguments_list else None,
        raw=file_contents[cursor.extent.start.offset:body_end.offset] if has_body else None,
        return_type=cursor.type.get_result().spelling,
        name=cursor.spelling,
        static=cursor.storage_class.name == 'STATIC',
        inline=is_inline,
        variadic=has_arguments_list and cursor.type.is_function_variadic()
    )


@cached_filename
def get_functions(file: str) -> List[Function]:
    file_contents = '\n'.join(get_lines(file))

    parsed = clang.cindex.Index.create().parse(file).cursor
    new_functions = []

    if parsed.kind.name == 'TRANSLATION_UNIT':
        for tu_child in [
            c for c in parsed.get_children()
            if c.kind.name == 'FUNCTION_DECL' and str(c.location.file) == file
        ]:
            new_functions.append(_get_function_from_clang_cursor(tu_child, file_contents))
    return new_functions



@cached_filename
def get_functions_legacy(file: str) -> List[Function]:
    """
    Get all functions in a file using the legacy regex method.
    It is only used in order to detect functions not detected by Clang (e.g. GCC nested functions).
    get_functions() should be used instead.

    :param file: The file name
    :return: A list of functions
    """
    raw = '\n'.join(get_lines(file, replace_comments=True, replace_stringlits=True))
    uncommented = remove_attributes(raw)
    matches = re.finditer(FUNCTION_REGEX, uncommented)
    functions = []
    for match in matches:
        before_function_len = len(match.group("beforeFunction"))
        match_start = match.start() + before_function_len + 1
        raw_match = match.group()[before_function_len + 1:]
        if match.group("functionStartChar") == ';':
            function_body = None
        else:
            function_body = __get_function_body(file, match.end() - 1)
        proto_start_line = raw.count('\n', 0, match.start()) + match.group("beforeFunction").count('\n') + 1
        proto_start_column = get_column(raw, proto_start_line, match_start - 1)
        proto_end_line = proto_start_line + raw_match.count('\n')
        proto_end_column = get_column(raw, proto_end_line, match.end() - 1)
        prototype_raw = raw_match[:match.end() - 1]
        functions.append(Function(
            prototype=Section(
                line_start=proto_start_line,
                line_end=proto_end_line,
                column_start=proto_start_column,
                column_end=proto_end_column,
                raw=prototype_raw
            ),
            body=function_body,
            raw=prototype_raw + (function_body.raw if function_body else ""),
            return_type=match.group("type"),
            name=match.group("name"),
            arguments=__get_arguments_from_string(match.group("args")),
        ))
    return functions


def get_function_body_tokens(file: str, func: Function) -> list[Token]:
    """
    Get the tokens of the function body, between and excluding the body braces.

    :param file: The file name
    :param func: The function
    :return:
    """
    return vera.getTokens(
        file,
        func.body.line_start,
        func.body.column_start,
        func.body.line_end,
        func.body.column_end,
        []
    )[1:]


def _contains_ambiguous_statement(tokens: list[Token]) -> bool:
    i = 0
    while i < len(tokens) and tokens[i].name == 'identifier':
        i += 1
    if i >= len(tokens) or i == 0:
        return False
    parentheses_pairs = 0
    while i < len(tokens) and tokens[i].name == 'leftparen':
        parentheses_pairs += 1
        i, _ = skip_interval(tokens, i, 'leftparen', 'rightparen')
        i += 1
    return parentheses_pairs == 2


def _starts_with_identifier_and_leftparen(tokens: list[Token]) -> bool:
    return (len(tokens) >= 2
            and tokens[0].name == 'identifier'
            and tokens[1].name == 'leftparen')


def _get_amount_of_variable_defining_identifiers(tokens: list[Token]) -> int:
    """
    Gets the amount of identifiers that are not inside brackets, and are not related to structure field access.

    :param tokens:
    :return:
    """
    amount = 0
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # "new" is included as it is a valid C identifier, but a reserved keyword in C++
        if token.name in ['identifier', 'new']:
            if i + 1 < len(tokens) and tokens[i + 1].name == 'leftparen':
                return 0
            if ((i + 1 >= len(tokens) or tokens[i + 1].name not in STRUCTURE_ACCESS_OPERATORS_TOKENS)
                and (i - 1 < 0 or tokens[i - 1].name not in STRUCTURE_ACCESS_OPERATORS_TOKENS)):
                amount += 1
        elif token.name == 'leftbracket':
            i, _ = skip_interval(tokens, i, 'leftbracket', 'rightbracket')
        if tokens[i].name == 'rightbracket' and i + 1 < len(tokens) and tokens[i + 1].name == 'leftparen':
            # This is a function call following an indexing
            return 0
        i += 1
    return amount


class UnsureBool(Enum):
    TRUE = 'True'
    FALSE = 'False'
    UNSURE = 'Unsure'

    @staticmethod
    def from_bool(value: bool | None) -> 'UnsureBool':
        if value is None:
            return UnsureBool.UNSURE
        return UnsureBool.TRUE if value else UnsureBool.FALSE


def is_variable_declaration(statement: list[Token]) -> UnsureBool:
    if not statement:
        return UnsureBool.FALSE
    if statement[0].name in TYPES_TOKENS:
        return UnsureBool.TRUE

    tokens_before_assign = []
    i = 0
    while i < len(statement):
        token = statement[i]
        if token.name == 'assign':
            break
        if token.name == 'leftbracket':
            tokens_before_assign.append(token)
            new_i, skipped_token = skip_interval(
                statement, statement.index(token), 'leftbracket', 'rightbracket'
            )
            i = new_i + 1
            tokens_before_assign += skipped_token
            tokens_before_assign.append(statement[new_i])
        else:
            tokens_before_assign.append(token)
            i += 1
    if not tokens_before_assign:
        return UnsureBool.UNSURE
    if tokens_before_assign[0].name == 'identifier':
        if _contains_ambiguous_statement(tokens_before_assign):
            return UnsureBool.UNSURE
        if (_get_amount_of_variable_defining_identifiers(tokens_before_assign) >= 2
                and not _starts_with_identifier_and_leftparen(tokens_before_assign)
                and not any(map(lambda t: t.name in ASSIGN_TOKENS, tokens_before_assign))):
            return UnsureBool.TRUE
    return UnsureBool.FALSE


def skip_interval(
        tokens: list[Token],
        i: int,
        start_token_name: str,
        end_token_name: str
) -> Tuple[int, list[Token]]:
    """
    Skips an interval of tokens, starting from the token at index i,
    and ending at the first token with name end_token_name

    :param tokens: The tokens
    :param i: The index of the first token
    :param start_token_name: The name of the starting token
    :param end_token_name: The name of the ending token
    :return: The index of the ending token, and the skipped tokens
    """
    depth = 0
    skipped_tokens = []
    while i < len(tokens):
        token = tokens[i]
        if token.name == start_token_name:
            depth += 1
        elif token.name == end_token_name:
            depth -= 1
            if depth == 0:
                break
        # Starting token is not included in skipped tokens
        if depth != 0 and (token.name != start_token_name or depth != 1):
            skipped_tokens.append(token)
        i += 1
    return i, skipped_tokens


@dataclass
class _StatementType:
    ending_tokens: list[str]
    interval_tokens: tuple[str, str] | None = None
    end_after_first_skip: bool = False


_CONTROL_STRUCTURE_STATEMENT = _StatementType(
    ending_tokens=['leftbrace', 'semicolon'],
    interval_tokens=('leftparen', 'rightparen'),
    end_after_first_skip=True
)
_CASE_AND_DEFAULT_STATEMENT = _StatementType(
    ending_tokens=['colon']
)
_OTHER_STATEMENT = _StatementType(
    ending_tokens=['semicolon'],
    interval_tokens=('leftbrace', 'rightbrace')
)


def _get_statement_type(first_statement_token: Token) -> _StatementType | None:
    if first_statement_token.name in CONTROL_STRUCTURE_TOKENS:
        return _CONTROL_STRUCTURE_STATEMENT
    if first_statement_token.name in ['case', 'default']:
        return _CASE_AND_DEFAULT_STATEMENT
    if first_statement_token.name != 'rightbrace':
        return _OTHER_STATEMENT
    return None


def is_else(tokens: list[Token], i: int) -> bool:
    return i < len(tokens) and tokens[i].name == 'else' and (i + 1 >= len(tokens) or tokens[i + 1].name != 'if')


def _get_statement_tokens(tokens: list[Token], i: int, statement_type: _StatementType):
    statement_tokens = []
    skip_happened = False
    # Special handling for else (not for an else-if)
    is_else_special_case = is_else(tokens, i)
    if is_else_special_case:
        statement_tokens.append(tokens[i])
        skip_happened = True
    while not is_else_special_case and i < len(tokens) and tokens[i].name not in statement_type.ending_tokens:
        statement_tokens.append(tokens[i])
        if statement_type.interval_tokens and tokens[i].name == statement_type.interval_tokens[0]:
            i, skipped_tokens = skip_interval(tokens, i, statement_type.interval_tokens[0],
                                              statement_type.interval_tokens[1])
            statement_tokens += skipped_tokens
            if i < len(tokens):
                statement_tokens.append(tokens[i])
            if statement_type.end_after_first_skip:
                skip_happened = True
                break
        i += 1
    if skip_happened and i + 1 < len(tokens) and tokens[i + 1].name in statement_type.ending_tokens:
        statement_tokens.append(tokens[i + 1])
        i += 1
    elif not skip_happened and i < len(tokens) and tokens[i].name in statement_type.ending_tokens:
        statement_tokens.append(tokens[i])
    return statement_tokens, i


def get_function_statements(tokens: list[Token]) -> list[list[Token]]:
    filtered_tokens = filter_out_non_semantic_tokens(tokens)
    statements = []
    i = 0
    while i < len(filtered_tokens):
        current_statement = []

        statement_type = _get_statement_type(filtered_tokens[i])
        if statement_type:
            statement_tokens, i = _get_statement_tokens(filtered_tokens, i, statement_type)
            current_statement += statement_tokens
        else:
            current_statement.append(filtered_tokens[i])

        statements.append(current_statement)

        i += 1
    return statements


def for_each_function_with_statements(file: str, handler_func: Callable[[list[list[Token]]], None]) -> None:
    functions = get_functions(file)
    for func in functions:
        if func.body is None:
            continue
        function_tokens = get_function_body_tokens(file, func)
        statements = get_function_statements(function_tokens)
        handler_func(statements)
