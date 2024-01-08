import vera

from utils import is_header_file, is_source_file, is_makefile, get_lines


def check_trailing_spaces():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file) and not is_makefile(file):
            continue
        for line_number, line in enumerate(get_lines(file), start=1):
            # Reports for every trailing space, not just once per offending line
            line_without_break = line.rstrip("\r\n")
            for _ in range(len(line_without_break) - len(line_without_break.rstrip())):
                vera.report(file, line_number, "MINOR:C-G7")


check_trailing_spaces()
