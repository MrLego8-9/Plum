from dataclasses import dataclass

import vera
from utils import is_source_file, is_header_file, Token, CONTROL_STRUCTURE_TOKENS
from utils.functions import for_each_function_with_statements

# The maximum depth of nested control structures allowed
# before reporting a violation.
MAX_DEPTH_ALLOWED = 2


@dataclass
class Branching:
    depth: int
    is_else_if: bool
    has_braces: bool


def _get_conditional_branching_depth_item(
        statement: list[Token],
        current_depth: int,
        just_left_else_if: bool
) -> Branching | None:
    is_else_if = len(statement) >= 2 and statement[0].type == 'else' and statement[1].type == 'if'
    is_else_after_else_if = statement[0].type == 'else' and just_left_else_if
    depth_to_add = 1
    if is_else_if:
        depth_to_add += 1
    if is_else_after_else_if:
        depth_to_add += 1
    if current_depth + depth_to_add > MAX_DEPTH_ALLOWED:
        vera.report(statement[0].file, statement[0].line, 'MAJOR:C-C1')
    if statement[-1].type != 'semicolon':
        return Branching(depth_to_add, is_else_if, statement[-1].type == 'leftbrace')
    return None


def _unstack_depth_items(statement: list[Token], depth: list[Branching]) -> tuple[list[Branching], bool]:
    just_left_else_if = False
    if (len(statement) == 1 and statement[0].type == 'rightbrace') or not depth[-1].has_braces:
        branching_left = depth.pop(-1)
        just_left_else_if = branching_left.is_else_if
        while len(depth) > 0 and not depth[-1].has_braces:
            branching_left = depth.pop(-1)
            just_left_else_if = branching_left.is_else_if
    return depth, just_left_else_if


def _check_conditional_branching(statements: list[list[Token]]):
    # list of tuple of depth level and braceless state
    depth: list[Branching] = []
    just_left_else_if = False
    for statement in statements:
        if statement[0].type in CONTROL_STRUCTURE_TOKENS:
            depth_item = _get_conditional_branching_depth_item(
                statement,
                sum(d.depth for d in depth),
                just_left_else_if
            )
            if depth_item is not None:
                depth.append(depth_item)
        elif len(depth) > 0:
            depth, just_left_else_if = _unstack_depth_items(statement, depth)



def check_conditional_branching():
    for file in vera.getSourceFileNames():
        if not (is_source_file(file) or is_header_file(file)):
            continue

        for_each_function_with_statements(file, _check_conditional_branching)


check_conditional_branching()
