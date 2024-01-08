import re

import vera
from utils import is_source_file, is_header_file, is_makefile, get_lines

MAKEFILE_HEADER_REGEX = re.compile(
    r'^##\n'
    r'## EPITECH PROJECT, [1-9][0-9]{3}\n'
    r'## \S.+\n'
    r'## File description:\n'
    r'(## .*\n)+'
    r'##(\n|$)')

C_HEADER_REGEX = re.compile(
    r'^/\*\n'
    r'\*\* EPITECH PROJECT, [1-9][0-9]{3}\n'
    r'\*\* \S.+\n'
    r'\*\* File description:\n'
    r'(\*\* .*\n)+'
    r'\*/(\n|$)')


def check_epitech_header():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file) and not is_makefile(file):
            continue
        raw = '\n'.join(get_lines(file))
        if (is_source_file(file) or is_header_file(file)) and not re.match(C_HEADER_REGEX, raw):
            vera.report(file, 1, 'MINOR:C-G1')
        if is_makefile(file) and not re.match(MAKEFILE_HEADER_REGEX, raw):
            vera.report(file, 1, 'MINOR:C-G1')


check_epitech_header()
