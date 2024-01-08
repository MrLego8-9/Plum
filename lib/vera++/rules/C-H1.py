import vera
from utils import is_source_file, is_header_file
from utils.functions import get_functions, Function

FORBIDDEN_SOURCE_FILE_DIRECTIVES = ['typedef', 'pp_define']


def check_forbidden_directives():
    for file in vera.getSourceFileNames():
        if not is_source_file(file):
            continue
        for token in vera.getTokens(file, 1, 0, -1, -1, FORBIDDEN_SOURCE_FILE_DIRECTIVES):
            vera.report(file, token.line, 'MAJOR:C-H1')


def _is_function_allowed_in_source_file(function: Function) -> bool:
    if function.body is None:
        return False
    if function.static and function.inline:
        return False
    return True


def _is_function_allowed_in_header_file(function: Function) -> bool:
    if function.body is None:
        return True
    return function.static and function.inline


def _is_function_allowed_in_file(function: Function, file: str) -> bool:
    if is_source_file(file):
        return _is_function_allowed_in_source_file(function)
    if is_header_file(file):
        return _is_function_allowed_in_header_file(function)
    return False


def check_functions():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue
        functions = get_functions(file)
        for function in functions:
            if not _is_function_allowed_in_file(function, file):
                vera.report(file, function.prototype.line_start, "MAJOR:C-H1")


check_forbidden_directives()
check_functions()
