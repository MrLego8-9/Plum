from functools import wraps


def cached(hash_method):
    # it would be event better to have the __cache at file scope but
    # the check_code_quality force us to put it there...
    __cache = {}

    def wrapper(func):

        @wraps(func)
        def wrapped(*args, **kwargs):
            key = (func.__name__, hash_method(*args, **kwargs))
            cached_value = __cache.get(key)

            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            __cache[key] = result
            return result

        return wrapped
    return wrapper


def cached_filename(func):
    # Set within a function
    # to avoid check_code_quality "global variables case" report
    # cached_filename = cached(lambda filename, *_, **__: filename)
    return cached(lambda filename, *_, **__: filename)(func)
