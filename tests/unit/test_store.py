import unittest
import subprocess
import shlex
import functools
import sys
import os
import time
from redis.exceptions import TimeoutError, ConnectionError
from mock import MagicMock

sys.path.append(os.path.join(os.getcwd(), ''))
from store import Store, RedisStore
from tests.cases import cases


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store(RedisStore())
        self.redis_store = RedisStore()
        self.redis_start()

    def redis_start(self):
        subprocess.Popen(shlex.split('redis-server'), shell=False, env=None, stdout=subprocess.PIPE)
        time.sleep(0.1)

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_ok_store_get(self, value):
        key, val = value
        self.store.cache_set(key, val, 1)
        self.assertEqual(val, self.store.get(key))
        self.assertIsInstance(val, basestring)

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_ok_store_cache_get(self, value):
        key, val = value
        self.store.cache_set(key, val, 1)
        self.assertEqual(val, self.store.cache_get(key))
        self.assertIsInstance(val, basestring)

    @cases(['key_one','key_two'])
    def test_nonexistent_key_store_cache_get(self, key):
        self.assertIsNone(self.store.cache_get(key))

    @cases(['key_one','key_two'])
    def test_nonexistent_key_store_get(self, key):
        self.assertIsNone(self.store.get(key))

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_ok_redis_store_get(self, value):
        key, val = value
        self.redis_store.set(key, val, 1)
        self.assertEqual(val, self.redis_store.get(key))
        self.assertIsInstance(val, basestring)

    @cases(['key_one','key_two'])
    def test_nonexistent_key_redis_store_get(self, key):
        self.redis_store.redis_base.flushall()
        self.assertIsNone(self.redis_store.get(key))

    def test_redis_connection_error(self):
        redis_store = RedisStore()
        redis_store.get = MagicMock(side_effect=ConnectionError())
        redis_store.set = MagicMock(side_effect=ConnectionError())
        
        store = Store(redis_store)
        self.assertEqual(store.cache_get("key"), None)
        self.assertEqual(store.cache_set("key", "value"), None)
        self.assertEqual(redis_store.get.call_count, Store.MAX_ATTEMPT)
        self.assertEqual(redis_store.set.call_count, Store.MAX_ATTEMPT)
        with self.assertRaises(ConnectionError):
            redis_store.get('key')
        with self.assertRaises(ConnectionError):
            redis_store.set('key', 'value', 10)

    def test_redis_timeout_error(self):
        redis_store = RedisStore()
        redis_store.get = MagicMock(side_effect=TimeoutError())
        redis_store.set = MagicMock(side_effect=TimeoutError())
        store = Store(redis_store)
        self.assertEqual(store.cache_get("key"), None)
        self.assertEqual(store.cache_set("key", "value"), None)
        self.assertEqual(redis_store.get.call_count, Store.MAX_ATTEMPT)
        self.assertEqual(redis_store.set.call_count, Store.MAX_ATTEMPT)
        with self.assertRaises(TimeoutError):
            redis_store.get('key')
        with self.assertRaises(TimeoutError):
            redis_store.set('key', 'value', 10)


if __name__ == "__main__":
    unittest.main()
