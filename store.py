import redis
import time
from redis.exceptions import TimeoutError, ConnectionError
from functools import wraps


def connection_attempt(exceptions, tries=3, timeout=0.2):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for _ in range(tries):
                try:
                    return f(*args, **kwargs)
                except exceptions:
                    time.sleep(timeout)
        return wrapper
    return decorator


class RedisStore(object):
    def __init__(self, host='localhost', db=None, port=6379, timeout=None):
        self.redis_base = redis.Redis(
            host=host,
            port=port,
            db=db or 0,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            decode_responses=True)

    def get(self, key):
        return self.redis_base.get(key)

    def set(self, key, value, expire=None):
        return self.redis_base.set(key, value, ex=expire)


class Store(object):
    MAX_ATTEMPT = 3
    TIMEOUT = 0.2

    def __init__(self, store):
        self.store = store

    def get(self, key):
        for _ in range(self.MAX_ATTEMPT):
            try:
                return self.store.get(key)
            except (TimeoutError, ConnectionError):
                time.sleep(self.TIMEOUT)

    @connection_attempt((TimeoutError, ConnectionError), MAX_ATTEMPT, TIMEOUT)
    def cache_get(self, key):
        return self.store.get(key)

    @connection_attempt((TimeoutError, ConnectionError), MAX_ATTEMPT, TIMEOUT)
    def cache_set(self, key, value, expire=None):
        return self.store.set(key, value, expire=expire)
