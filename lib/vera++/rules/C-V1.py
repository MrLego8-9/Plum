import io
import re

import vera
from utils import is_source_file, is_header_file, get_lines

ALLOWED_TYPES = [
    "sfBlack",
    "sfBlendAdd",
    "sfBlendAlpha",
    "sfBlendMultiply",
    "sfBlendNone",
    "sfBlue",
    "sfCircleShape",
    "sfClock",
    "sfColor",
    "sfContext",
    "sfConvexShape",
    "sfCursor",
    "sfCyan",
    "sfFloatRect",
    "sfFont",
    "sfGreen",
    "sfImage",
    "sfIntRect",
    "sfJoystick",
    "sfKeyboard",
    "sfListener",
    "sfMagenta",
    "sfMicroseconds",
    "sfMilliseconds",
    "sfMouse",
    "sfMouseButtonEvent",
    "sfMusic",
    "sfMutex",
    "sfRectangleShape",
    "sfRed",
    "sfRenderStates",
    "sfRenderTexture",
    "sfRenderWindow",
    "sfSeconds",
    "sfSensor",
    "sfShader",
    "sfShape",
    "sfSleep",
    "sfSound",
    "sfSoundBuffer",
    "sfSoundBufferRecorder",
    "sfSoundRecorder",
    "sfSoundStream",
    "sfSprite",
    "sfText",
    "sfTexture",
    "sfThread",
    "sfTime",
    "sfTouch",
    "sfTransform",
    "sfTransformable",
    "sfTransparent",
    "sfVertexArray",
    "sfVideoMode",
    "sfView",
    "sfWhite",
    "sfWindow",
    "sfYellow",
    "sfBool",
    "sfFtp",
    "sfFtpDirectoryResponse",
    "sfFtpListingResponse",
    "sfFtpResponse",
    "sfGlslIvec2",
    "sfGlslVec2",
    "sfGlslVec3",
    "sfHttp",
    "sfHttpRequest",
    "sfHttpResponse",
    "sfInputStream",
    "sfInputStreamGetSizeFunc",
    "sfInputStreamReadFunc",
    "sfInputStreamSeekFunc",
    "sfInputStreamTellFunc",
    "sfInt16",
    "sfInt32",
    "sfInt64",
    "sfInt8",
    "sfPacket",
    "sfShapeGetPointCallback",
    "sfSocketSelector",
    "sfSoundBuffer",
    "sfSoundBufferRecorder",
    "sfSoundRecorder",
    "sfSoundRecorderProcessCallback",
    "sfSoundRecorderStartCallback",
    "sfSoundRecorderStopCallback",
    "sfSoundStream",
    "sfSoundStreamChunk",
    "sfSoundStreamGetDataCallback",
    "sfSoundStreamSeekCallback",
    "sfTcpListener",
    "sfTcpSocket",
    "sfUdpSocket",
    "sfUint16",
    "sfUint32",
    "sfUint64",
    "sfUint8",
    "sfVector2f",
    "sfVector2u",
    "sfVector2i",
    "sfVector3f",
    "sfVector3u",
    "sfVector3i",
    "sfWindowHandle",
    "userData",
    "FILE",
    "DIR",
    "Elf_Byte",
    "Elf32_Sym",
    "Elf32_Off",
    "Elf32_Addr",
    "Elf32_Section",
    "Elf32_Versym",
    "Elf32_Half",
    "Elf32_Sword",
    "Elf32_Word",
    "Elf32_Sxword",
    "Elf32_Xword",
    "Elf32_Ehdr",
    "Elf32_Phdr",
    "Elf32_Shdr",
    "Elf32_Rel",
    "Elf32_Rela",
    "Elf32_Dyn",
    "Elf32_Nhdr",
    "Elf64_Sym",
    "Elf64_Off",
    "Elf64_Addr",
    "Elf64_Section",
    "Elf64_Versym",
    "Elf64_Half",
    "Elf64_Sword",
    "Elf64_Word",
    "Elf64_Sxword",
    "Elf64_Xword",
    "Elf64_Ehdr",
    "Elf64_Phdr",
    "Elf64_Shdr",
    "Elf64_Rel",
    "Elf64_Rela",
    "Elf64_Dyn",
    "Elf64_Nhdr",
    "_Bool",
    "WINDOW"
]

_MODIFIERS = (
    "inline",
    "static",
    "unsigned",
    "signed",
    "short",
    "long",
    "volatile",
    "struct",
)

_MODIFIERS_REGEX = '|'.join(_MODIFIERS)
FUNCTION_PROTOTYPE_REGEX = (
    fr"^[\t ]*(?P<modifiers>(?:(?:{_MODIFIERS_REGEX})[\t ]+)*)"
    r"(?!else|typedef|return)(?P<type>\w+)\**[\t ]+\**[\t ]*\**[\t ]*"
    r"(?P<name>\w+)(?P<spaces>[\t ]*)"
    r"\((?P<parameters>[\t ]*"
    r"(?:(void|(\w+\**[\t ]+\**[\t ]*\**\w+[\t ]*(,[\t \n]*)?))+|)[\t ]*)\)"
    r"[\t ]*"
    r"(?P<endline>;\n|\n?{*\n){1}"
)

def _get_lines_without_comments(filepath: str) -> str:
    buf = io.StringIO()

    for line in get_lines(filepath, replace_comments=True):
        buf.write(line)
        buf.write('\n')

    return buf.getvalue()


def check_function_return_type():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        s = _get_lines_without_comments(file)
        p = re.compile(FUNCTION_PROTOTYPE_REGEX, re.MULTILINE)
        for search in p.finditer(s):
            line_start = s.count('\n', 0, search.start()) + 1
            if (
                search.group('type')
                and not re.match("^[a-z][a-z0-9_]*$", search.group('type'))
                and search.group('type') not in ALLOWED_TYPES
            ):
                vera.report(file, line_start, "MINOR:C-V1")


def check_macro_names():
    for file in vera.getSourceFileNames():
        if not is_source_file(file) and not is_header_file(file):
            continue

        defines = vera.getTokens(file, 1, 0, -1, -1, ["pp_define"])

        for df in defines:
            line = vera.getLine(file, df.line)
            index = line.find("define")

            if index == -1:
                continue

            cut = line[index + len("define"):].lstrip()
            end_cut = min(map(cut.find, " \t\n("))

            if end_cut == -1:
                macro_name = cut.strip()
            else:
                macro_name = cut[:end_cut].strip()
            if not re.match(r"[A-Z_$]([$A-Z_0-9]+)", macro_name):
                vera.report(file, df.line, "MINOR:C-V1")

check_function_return_type()
check_macro_names()
