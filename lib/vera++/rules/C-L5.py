import vera
from utils import is_header_file, is_source_file
from utils.functions import is_variable_declaration, for_each_function_with_statements, UnsureBool, skip_interval


def is_declaring_multiple_variables(statement) -> bool:
    declaration = []
    i = 0
    while i < len(statement):
        token = statement[i]
        if token.name == 'assign':
            break
        if token.name == 'leftparen':
            i, _ = skip_interval(statement, i, 'leftparen', 'rightparen')
        else:
            declaration.append(token)
        i += 1
    return len(list(filter(lambda t: t.name == 'comma', declaration))) > 0

def _check_variable_declarations_for_function(statements):
    declaration_zone = True
    for statement in statements:
        variable_declaration = is_variable_declaration(statement)
        if variable_declaration == UnsureBool.TRUE:
            if not declaration_zone or is_declaring_multiple_variables(statement):
                vera.report(
                    statement[0].file,
                    statement[0].line,
                    "MAJOR:C-L5",
                )
        elif variable_declaration == UnsureBool.FALSE:
            declaration_zone = False

def check_variable_declarations():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue
        for_each_function_with_statements(file, _check_variable_declarations_for_function)


check_variable_declarations()
