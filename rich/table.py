class Table:
    def __init__(self, title: str | None = None, show_header: bool = True, header_style: str | None = None):
        self.title = title
        self.columns = []
        self.rows = []
    def add_column(self, name):
        self.columns.append(name)
    def add_row(self, *values):
        self.rows.append(values)
    def __str__(self):
        lines = []
        if self.title:
            lines.append(self.title)
        for row in self.rows:
            lines.append(" | ".join(str(v) for v in row))
        return "\n".join(lines)
