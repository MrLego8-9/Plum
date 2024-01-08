import vera
from utils import is_source_file, is_header_file
from utils.functions import get_functions

MAX_ARGS_COUNT = 4


def check_no_empty_parameters_list():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        functions = get_functions(file)
        for function in functions:
            if function.arguments is None:
                vera.report(file, function.prototype.line_start, "MAJOR:C-F6")


check_no_empty_parameters_list()
