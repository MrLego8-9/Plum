from .section import Section

class Function:

    # pylint: disable=R0913, R0902
    def __init__(
        self,
        prototype: Section,
        body: Section | None,
        raw: str,
        return_type: str,
        name: str,
        arguments: list[str] | None,
        static: bool = False,
        inline: bool = False,
        variadic: bool = False
    ):
        self.prototype = prototype
        self.body = body
        self.raw = raw
        self.return_type = return_type
        self.name = name
        self.arguments = arguments
        self.static = static
        self.inline = inline
        self.variadic = variadic

    def __str__(self):
        base_str =(f'{"Static function" if self.static else "Function"}: {self.name} with prototype {self.prototype}'
                   f' returning {self.return_type}')
        if self.arguments is not None:
            if len(self.arguments) == 0:
                base_str += ', no arguments'
            else:
                base_str += f', arguments {self.arguments}'
        else:
            base_str += ', no defined argument list'
        if self.body:
            return f'{base_str} and body {self.body} (raw: "{self.body.raw}")'
        return f'{base_str} and no body'

    def __repr__(self):
        return str(self)

    def get_arguments_count(self) -> int:
        if self.arguments is None:
            return 0
        return len(self.arguments) + (1 if self.variadic else 0)
