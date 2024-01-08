import vera

from utils import is_header_file, is_source_file


def is_abusive_macro(line: str) -> bool:
    # Macro should fit in a single line
    # and contain a single statement
    return line.endswith('\\') or ';' in line


def check_macro_size():
    for file in vera.getSourceFileNames():
        if not is_header_file(file) and not is_source_file(file):
            continue

        defines = vera.getTokens(file, 1, 0, -1, -1, ['pp_define'])

        for df in defines:
            line = vera.getLine(file, df.line).rstrip()

            if is_abusive_macro(line):
                vera.report(file, df.line, "MAJOR:C-H3")


if __name__ == "__main__":
    check_macro_size()
