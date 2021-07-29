import logging


def exception_handler(function_to_wrap):
    def wrapper(*args, **kwargs):
        try:
            return function_to_wrap(*args, **kwargs)
        except Exception as e:
            logging.warning(e)

    return wrapper
