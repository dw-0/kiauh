
def emit_cast(var) -> str:
    """Generate a human-readable typecast such as for logging"""
    if var in (None, False, True):
        return str(var)
    return "{}({})".format(type(var).__name__, repr(var))
