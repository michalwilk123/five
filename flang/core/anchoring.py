from flang.structures import VirtualFileRepresentation

def join_(iterable, _with: str = ""):
    for item in iterable:
        if isinstance(item, str):
            return _with.join(iterable)
        elif isinstance(item, VirtualFileRepresentation):
            return list(iterable)

        raise RuntimeError

# def realize
