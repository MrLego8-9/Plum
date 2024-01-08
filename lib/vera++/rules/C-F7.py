import re

import vera
from utils import is_header_file, is_source_file
from utils.functions import get_functions


def _remove_modifiers(arg: str, modifiers: list[str]) -> str:
    modifierless_arg = arg
    for modifier in modifiers:
        if re.fullmatch(rf'(^|\W){modifier}(\W.*)?$', modifierless_arg):
            modifierless_arg = modifierless_arg.replace(modifier, '')
    return modifierless_arg


def _check_arguments(file: str, line: int, arg: str) -> None:
    normalized_arg = arg.replace('\t', ' ')
    while '  ' in normalized_arg:
        normalized_arg = normalized_arg.replace('  ', ' ')
    normalized_arg = normalized_arg.strip()

    split_arg = []
    for split_arg_item in normalized_arg.split(' '):
        modifierless_arg = _remove_modifiers(split_arg_item, ['const', 'volatile', 'restrict'])
        if modifierless_arg != '':
            split_arg.append(modifierless_arg)

    if 'struct' not in split_arg or len(split_arg) < 3:
        # struct should have 2 at least 2 words after them
        # eg: struct foo_s *my_struct
        return

    _, struct_typ, name, *_ = split_arg
    if not name.startswith('*') and not struct_typ.endswith('*'):
        vera.report(file, line, "MAJOR:C-F7")


def check_no_structure_copy_as_parameter():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        for function in get_functions(file):
            if function.arguments is None:
                continue
            for arg in function.arguments:
                _check_arguments(file, function.prototype.line_start, arg)


check_no_structure_copy_as_parameter()
