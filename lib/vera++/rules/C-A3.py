import vera

from utils import is_source_file, is_header_file, is_makefile, get_lines


def check_file_end():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file) and not is_makefile(file):
            continue

        lines = get_lines(file)
        if lines[-1] != '':
            vera.report(file, len(lines), 'INFO:C-A3')


check_file_end()
