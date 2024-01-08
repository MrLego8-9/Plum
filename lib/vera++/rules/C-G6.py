import vera

from utils import is_header_file, is_source_file, is_makefile, get_lines


def check_carriage_return_character():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file) and not is_makefile(file):
            continue
        for line_number, line in enumerate(get_lines(file), start=1):
            if '\r' in line:
                vera.report(file, line_number, "MINOR:C-G6")


check_carriage_return_character()
