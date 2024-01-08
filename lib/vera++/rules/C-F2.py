import vera
from utils import is_source_file, is_header_file, is_lower_snakecase
from utils.functions import get_functions


def check_name_case():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue
        functions = get_functions(file)
        for function in functions:
            if function.body is None:
                continue
            if not is_lower_snakecase(function.name) or len(function.name.replace('_', '')) <= 2:
                vera.report(file, function.prototype.line_start, "MINOR:C-F2")


check_name_case()
