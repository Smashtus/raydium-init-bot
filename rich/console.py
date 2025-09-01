import builtins

class Console:
    def print(self, *args, **kwargs):
        for arg in args:
            builtins.print(arg)
