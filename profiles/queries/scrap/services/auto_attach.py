# auto_attach.py
from services.signal_handler import check_and_terminate


class AutoTerminateWrapper:
    def __init__(self, obj):

        self._obj = obj

    def __getattr__(self, name):
        attr = getattr(self._obj, name)

        if callable(attr):

            def wrapped_method(*args, **kwargs):
                check_and_terminate()  # Check before method call
                result = attr(*args, **kwargs)
                check_and_terminate()  # Check after method call
                return result

            return wrapped_method
        return attr
