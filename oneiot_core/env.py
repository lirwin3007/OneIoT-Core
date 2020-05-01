import os

def var(name, default):
    return os.getenv(name) if os.getenv(name) is not None else default
