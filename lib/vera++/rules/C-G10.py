import vera

from utils import is_source_file, is_header_file


def check_inline_assembly_usage():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue
        for asm_token in vera.getTokens(file, 1, 0, -1, -1, ['asm', 'identifier']):
            if asm_token.name == 'asm' or asm_token.value == '__asm__':
                vera.report(file, asm_token.line, 'FATAL:C-G10')


check_inline_assembly_usage()
