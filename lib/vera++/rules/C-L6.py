import vera
from utils import is_header_file, is_source_file, is_line_empty
from utils.functions import get_functions, get_function_statements, is_variable_declaration, get_function_body_tokens, \
    UnsureBool

def _get_variable_declaration_status_for_each_line(function_statements) -> list[UnsureBool]:
    return list(map(is_variable_declaration, function_statements))

def _get_line_number_after_declarations(
        statements: list[list[vera.Token]],
        declaration_statuses: list[UnsureBool]
) -> int | None:
    declarations_present = False
    for i, statement in enumerate(statements):
        declaration_status = declaration_statuses[i]
        if declaration_status == UnsureBool.TRUE:
            declarations_present = True
        else:
            return statement[0].line if declarations_present else None
    return None

def _has_declaration_zone(variable_declarations: list[UnsureBool]) -> UnsureBool:
    has_one_sure_declaration = False
    for declaration in variable_declarations:
        if declaration == UnsureBool.TRUE:
            has_one_sure_declaration = True
        elif declaration == UnsureBool.FALSE:
            break
        else:
            return UnsureBool.UNSURE
    return UnsureBool.from_bool(has_one_sure_declaration)

def _check_line_breaks_for_function(tokens, empty_lines: list[int]):
    function_statements = get_function_statements(tokens)
    variable_declarations = _get_variable_declaration_status_for_each_line(function_statements)
    has_declaration_zone = _has_declaration_zone(variable_declarations)

    unnecessary_empty_lines = empty_lines.copy()
    if has_declaration_zone == UnsureBool.TRUE:
        line_number_after_declarations = _get_line_number_after_declarations(function_statements, variable_declarations)
        mandatory_line_break = line_number_after_declarations - 1 if line_number_after_declarations is not None else None
        if mandatory_line_break:
            if mandatory_line_break not in empty_lines:
                vera.report(
                    tokens[0].file,
                    mandatory_line_break + 1,
                    "MINOR:C-L6",
                )
            else:
                # Remove the lowest empty line number adjacent to the mandatory line break,
                # so that in the case of a double line break, the first one is not reported,
                # as it is the one expected.
                line_break_to_remove = mandatory_line_break
                for line_number in range(mandatory_line_break - 1, 0, -1):
                    if line_number not in empty_lines:
                        break
                    line_break_to_remove = line_number
                unnecessary_empty_lines.remove(line_break_to_remove)
    elif has_declaration_zone == UnsureBool.UNSURE and len(empty_lines) > 0:
        unnecessary_empty_lines.pop(0)

    for line_number in unnecessary_empty_lines:
        vera.report(
            tokens[0].file,
            line_number,
            "MINOR:C-L6",
        )

def _get_function_empty_lines(file, line_start, line_end) -> list[int]:
    file_lines = vera.getAllLines(file)
    empty_lines = []
    for line_number in range(line_start, line_end + 1):
        if is_line_empty(file_lines[line_number - 1]):
            empty_lines.append(line_number)
    return empty_lines

def check_variable_declarations():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        functions = get_functions(file)
        for function in functions:
            if function.body is None:
                continue
            function_tokens = get_function_body_tokens(file, function)
            empty_lines = _get_function_empty_lines(file, function.body.line_start, function.body.line_end)
            _check_line_breaks_for_function(function_tokens, empty_lines)



check_variable_declarations()
