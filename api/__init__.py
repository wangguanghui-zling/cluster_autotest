#! /usr/bin/env python



from api._API import _API


__all__ = [
    "API"
]


class API(
    _API,
):
    def __init__(self):
        super().__init__()


API = API()
