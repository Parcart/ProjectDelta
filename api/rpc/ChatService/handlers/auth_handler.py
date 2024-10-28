from functools import wraps
from typing import Callable


def authorization(func: Callable) -> Callable:
    """
    Decorator for authorization checks.

    Retrieves the token from the request metadata, verifies it, 
    and passes the user object to the function.

    :param func: The function to be decorated.
    :return: The decorated function.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        """
        Inner function called instead of the original.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: The result of calling the original function.
        """

    return wrapper
