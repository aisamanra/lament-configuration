import typing


class SqliteExtDatabase:
    def __init__(self, path: typing.Optional[str]):
        pass

    def atomic(self):
        pass

    def init(self, path: str):
        pass

    def close(self):
        pass

    def create_tables(self, tables: typing.List[typing.Any], safe: bool = True):
        pass
