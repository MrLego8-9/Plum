class Section:

    # pylint: disable=R0913, R0902
    def __init__(
        self,
        line_start: int,
        line_end: int,
        column_start: int,
        column_end: int,
        raw: str
    ):
        self.line_start = line_start
        self.line_end = line_end
        self.column_start = column_start
        self.column_end = column_end
        self.raw = raw

    def __str__(self):
        return f'Section {self.line_start}:{self.column_start} to {self.line_end}:{self.column_end}'
