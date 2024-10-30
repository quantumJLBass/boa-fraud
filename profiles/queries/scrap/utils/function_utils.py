# function_utils.py
from functools import wraps

from services.applogging import logger
from services.signal_handler import check_and_terminate
from settings.settings import i


class Event:
    """
    A simple event system to trigger listeners for function calls.

    This class maintains a list of listeners and triggers them when events occur.
    """

    def __init__(self):
        self.listeners = []

    def register(self, listener):
        """
        Registers a listener to be triggered on an event.

        Args:
            listener (callable): A function to be triggered when the event occurs.
        """
        self.listeners.append(listener)

    def trigger(self, *args, **kwargs):
        """
        Triggers all registered listeners with optional arguments.

        Args:
            *args: Positional arguments to pass to the listener functions.
            **kwargs: Keyword arguments to pass to the listener functions.
        """
        logger.debug(
            f"Triggering {len(self.listeners)} listeners with arguments: {args}, {kwargs}"
        )
        for listener in self.listeners:
            listener(*args, **kwargs)


# Create a global event instance to handle function call events
on_function_call = Event()

# Register a listener to check for termination before and after every function call
on_function_call.register(check_and_terminate)


def sig_listener(func):
    """
    Decorator that attaches the termination listener before and after a function call.

    This ensures that any function wrapped with this decorator will trigger the
    `check_and_terminate` function before and after its execution to handle termination signals.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function with termination checks.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(
            f"🏁 Starting function: {func.__name__} with termination listener."
        )
        on_function_call.trigger()  # Before function call
        result = func(*args, **kwargs)
        on_function_call.trigger()  # After function call
        logger.debug(f"✅ Finished function: {func.__name__}")
        return result

    return wrapper


def loop_with_termination_check(iterable):
    """
    A loop wrapper that checks for termination on every iteration.

    This function ensures that `check_and_terminate` is called at each iteration of the loop,
    allowing clean shutdowns even during long-running processes.

    Args:
        iterable (iterable): The iterable to loop over.

    Yields:
        The items from the iterable, while checking for termination at each iteration.
    """
    logger.debug(f"{i()}🔄 Looping with termination check...")
    for item in iterable:
        check_and_terminate()  # Check at each iteration
        yield item

    logger.debug(f"{i()}✅ Finished looping with termination check.")
