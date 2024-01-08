import vera

from utils import is_source_file, is_header_file
from utils.functions import get_functions


def check_comment_inside_function():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue
        functions = get_functions(file)

        for function in functions:
            last_function_token = function.prototype if function.body is None else function.body
            comments = vera.getTokens(file, function.prototype.line_start, function.prototype.column_start,
                                      last_function_token.line_end, last_function_token.column_end,
                                      ['ccomment', 'cppcomment'])
            for comment in comments:
                vera.report(file, comment.line, "MINOR:C-F8")


check_comment_inside_function()
