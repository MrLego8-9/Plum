import vera

from utils import is_source_file, is_header_file, get_star_token_type, StarType, find_token_index


def __report(token):
    vera.report(token.file, token.line, "MINOR:C-V3")


def check_pointer_attachments():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        stars = vera.getTokens(file, 1, 0, -1, -1, ["star"])

        for star in stars:
            tokens = tuple(vera.getTokens(file, star.line, 0, star.line + 1, -1, []))
            i = find_token_index(tokens, star)
            star_type = get_star_token_type(tokens, i)

            if star_type not in {StarType.POINTER, StarType.DEREFENCE}:
                continue

            # Chained ptr (eg: char **)
            if tokens[i - 1].name == 'star':
                if tokens[i + 1].name == 'star':
                    continue
                if tokens[i + 1].name == 'space':
                    __report(star)
                continue

            if (
                tokens[i - 1].name not in {'space', 'leftparen', 'leftbracket'}
                and star_type == StarType.POINTER
            ):
                __report(star)

            # pointer edge case: ( *[])
            elif tokens[i - 2].name == "leftparen" and tokens[i - 1].name == "space":
                __report(star)

            if tokens[i + 1].name == "space":
                __report(star)


if __name__ == "__main__":
    check_pointer_attachments()
