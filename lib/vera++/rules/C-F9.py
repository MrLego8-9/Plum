import itertools
import vera

from utils import is_source_file, is_header_file
from utils.functions import get_functions_legacy, Function


def is_nested_function(parent: Function, child: Function):
    if parent.body is None or child.prototype is None:
        return False

    return (
        parent.body.line_start <= child.prototype.line_start
        and parent.body.line_end >= child.prototype.line_end
    )


def check_nested_functions():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        functions = get_functions_legacy(file)

        for fa, fb in itertools.combinations(functions, r=2):
            if is_nested_function(fa, fb):
                vera.report(file, fb.prototype.line_start, "MAJOR:C-F9")
            elif is_nested_function(fb, fa):
                vera.report(file, fa.prototype.line_start, "MAJOR:C-F9")


check_nested_functions()
