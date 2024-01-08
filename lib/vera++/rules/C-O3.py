import vera
from utils import is_header_file, is_source_file
from utils.functions import get_functions

MAX_FUNCTION_COUNT = 10
MAX_NON_STATIC_FUNCTION_COUNT = 5


def check_functions_count():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        functions = get_functions(file)
        function_count = 0
        non_static_function_count = 0
        for function in functions:
            if function.body is None:
                continue
            function_count += 1
            if not function.static:
                non_static_function_count += 1
                if non_static_function_count > MAX_NON_STATIC_FUNCTION_COUNT:
                    vera.report(file, function.prototype.line_start, "MAJOR:C-O3")
                    continue
            if function_count > MAX_FUNCTION_COUNT:
                vera.report(file, function.prototype.line_start, "MAJOR:C-O3")

check_functions_count()
