import re

import vera

from utils import is_header_file, is_source_file, get_lines, is_line_empty
from utils.functions import get_functions

from typing import List, Tuple, Sequence


def is_line_correctly_indented(line: str, in_function: bool) -> bool:
    # A well-indented line is considered to either be:
    # - an empty line;
    # - a line only comprised of spaces (which should not be considered a violation of the C-L2 rule,
    #   but a violation of the C-G7 rule);
    # - a line with any amount of 4 spaces groups (can be 0, notably for top-level statements),
    #   followed by a non-space and non-tabulation character.
    # - a line part of a comment block
    if is_line_empty(line):
        return True
    if line.endswith('*/'):
        return True
    indentation_regex = re.compile(r'^( *|( {4})*\S+.*)$')
    function_indentation_regex = re.compile(r'^( *|( {4})+\S+.*)$')
    if in_function:
        return function_indentation_regex.match(line) is not None
    return indentation_regex.match(line) is not None


def check_line_indentation():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        functions = get_functions(file)
        function_lines = []
        global_scope = []

        for function in functions:
            if function.body is not None:
                function_lines += range(function.body.line_start + 1, function.body.line_end)

        for line_number, line in enumerate(get_lines(file, replace_comments=True, replace_stringlits=True), start=1):
            if not is_line_correctly_indented(line, line_number in function_lines):
                vera.report(file, line_number, 'MINOR:C-L2')

            if line_number not in function_lines:
                global_scope.append((line_number, line))

        check_global_scope(file, global_scope)


def get_indent_level(line: str) -> int:
    spaces = 0
    for c in line:
        if c == ' ':
            spaces += 1
        elif c == '\t':
            spaces += 4
        else:
            break
    # round up
    return (spaces + 3) // 4


def iter_skip_comments(lines: Sequence[Tuple[int, str]]):
    # deeper clean after replace_comment
    in_comment = False
    in_string = False
    skip_next = False

    for lineno, line in lines:
        cleaned = ''

        for c, cnext in zip(line, line[1::] + ' '):
            if skip_next:
                skip_next = False
                continue

            if c == '"':
                in_string = not in_string

            if in_string:
                cleaned += c
                continue

            if not in_comment:
                if c == '/' and cnext in '/':
                    break

                if c == '/' and cnext == '*':
                    in_comment = True
                    continue

                cleaned += c
            elif c == '*' and cnext == '/':
                in_comment = False
                skip_next = True
        yield lineno, cleaned


def check_global_scope(file: str, global_scope: List[Tuple[int, str]]) -> None:
    depth = 0
    depth_stack = []
    depth_match = {
        '[': ']',
        '(': ')',
        '{': '}'
    }

    for lineno, line in iter_skip_comments(global_scope):
        depth_change = 0

        if not line or line.isspace():
            continue

        if line.lstrip(' \t').startswith('#'):
            continue

        postponed_depth_decrease = False

        for i, c in enumerate(line.lstrip(' \t')):
            if c in depth_match:
                depth_stack.append(depth_match[c])
                depth_change += 1
                depth += 1

            if depth_stack and c == depth_stack[-1]:
                depth_stack.pop()
                if i != 0 and depth_change == 0:
                    postponed_depth_decrease = True
                else:
                    depth -= 1
                    depth_change -= 1

        if get_indent_level(line) != depth and depth_change != 1:
            vera.report(file, lineno, "MINOR:C-L2")
        if postponed_depth_decrease:
            depth -= 1


check_line_indentation()
