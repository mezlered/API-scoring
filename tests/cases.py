import functools


def cases(cases, count={}):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(*new_args)
                except Exception, e:
                    count[f.__name__] = c.__repr__()
                    print '\n%s function error - %s case - %s' % (len(count), f.__name__, count[f.__name__])
                    raise e
        return wrapper
    return decorator
