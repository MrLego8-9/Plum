import vera
from utils import is_source_file, is_header_file
from utils.functions import get_functions

MAX_ARGS_COUNT = 4


def check_function_arguments():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        functions = get_functions(file)
        for function in functions:
            arguments_count = function.get_arguments_count()
            if arguments_count > MAX_ARGS_COUNT:
                for _ in range(arguments_count - MAX_ARGS_COUNT):
                    vera.report(file, function.prototype.line_start, "MAJOR:C-F5")


check_function_arguments()
