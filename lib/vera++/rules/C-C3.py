import vera

from utils import is_source_file, is_header_file


def check_goto_keyword():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue
        for goto_token in vera.getTokens(file, 1, 0, -1, -1, ['goto']):
            vera.report(file, goto_token.line, 'MAJOR:C-C3')


check_goto_keyword()
