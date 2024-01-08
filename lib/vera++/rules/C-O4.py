import re

import vera
from utils import is_header_file, is_source_file, get_filename_without_extension


def check_file_name():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        file_name = get_filename_without_extension(file)
        if not re.match(r'^[a-z]([a-z\d_]*[a-z\d])?$', file_name) or '__' in file_name:
            vera.report(file, 1, "MINOR:C-O4")


check_file_name()
