from typing import Type

class RaisesContext:
    def __enter__(self):
        pass
    def __exit__(self, _1, _2, _3):
        pass

def raises(e: Type[Exception]) -> RaisesContext:
    pass
