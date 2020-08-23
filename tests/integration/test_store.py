import hashlib
import functools
import unittest
import subprocess
import shlex
import time
import sys
import os
import redis
from datetime import datetime
import json

sys.path.append(os.path.join(os.getcwd(), ''))
import api
from store import Store, RedisStore
from tests.cases import cases


class TestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.redis_base = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            socket_timeout=None,
            socket_connect_timeout=None,
            decode_responses=True
        )

    def setUp(self):
        self.redis_start()

    def redis_start(self):
        subprocess.Popen(shlex.split('redis-server'), shell=False, env=None, stdout=subprocess.PIPE)
        time.sleep(0.2)

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_get(self, value):
        self.redis_base.flushall()
        store = Store(RedisStore())
        key, val = value
        self.redis_base.set(key, val)
        self.assertEqual(val, store.get(key))
        self.assertIsInstance(store.get(key), basestring)

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_get_nonexistent_key(self, value):
        store = Store(RedisStore())
        key = hashlib.md5("".join(value) + time.ctime()).hexdigest()
        self.assertIsNone(store.get(key))

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_get_store_not_available(self, value):
        store = Store(RedisStore(db=1))
        key = hashlib.md5("".join(value) + time.ctime()).hexdigest()
        self.assertIsNone(store.get(key))

    @cases([['key_one','value_one']])
    def test_set_expire(self, value):
        store = Store(RedisStore())
        key = hashlib.md5("".join(value) + time.ctime()).hexdigest()

        is_set = self.redis_base.set(key, value[1], 1)
        self.assertTrue(is_set)
        time.sleep(1.1)
        self.assertIs(None, store.get(key))


    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_cache_set(self, value):
        self.redis_base.flushall()
        store = Store(RedisStore())
        key, val = value
        is_set = store.cache_set(key, val, 10)
        self.assertTrue(is_set)
        self.assertEqual(val, self.redis_base.get(key))
        self.assertIsInstance(self.redis_base.get(key), basestring)

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_cache_get(self, value):
        self.redis_base.flushall()
        store = Store(RedisStore())
        key, val = value
        self.redis_base.set(key, val)
        self.assertEqual(val, store.cache_get(key))
        self.assertIsInstance(store.cache_get(key), basestring)

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_cache_get_nonexistent_key(self, value):
        store = Store(RedisStore())
        key = hashlib.md5("".join(value) + time.ctime()).hexdigest()
        self.assertIsNone(store.cache_get(key))

    @cases([['key_one','value_one']])
    def test_cache_set_expire(self, value):
        store = Store(RedisStore())
        key = hashlib.md5("".join(value) + time.ctime()).hexdigest()

        is_set = store.cache_set(key, value[1], 1)
        self.assertTrue(is_set)
        time.sleep(1.1)
        self.assertIs(None, self.redis_base.get(key))

    @cases([['key_one','value_one'],['key_two','value_two']])
    def test_cache_get_store_not_available(self, value):
        store = Store(RedisStore(db=1))
        key = hashlib.md5("".join(value) + time.ctime()).hexdigest()
        self.assertIsNone(store.cache_get(key))


class TestStoreInteraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.redis_base = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            socket_timeout=None,
            socket_connect_timeout=None,
            decode_responses=True
        )

    def redis_start(self):
        subprocess.Popen(shlex.split('redis-server'), shell=False, env=None, stdout=subprocess.PIPE)
        time.sleep(0.2)

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg).hexdigest()
    
    def get_key(self, arguments):
        birthday = ''
        if arguments.get('birthday', ''):
            birthday = datetime.strptime(arguments['birthday'], "%d.%m.%Y")
        key_parts = [
            arguments.get('first_name', ""),
            arguments.get('last_name', ""),
            str(arguments.get('phone', "")),
            birthday.strftime("%Y%m%d") if birthday else "",
        ]
        key = "uid:" + hashlib.md5("".join(key_parts)).hexdigest()
        return key

    def set_interests(self, redis_store):
        intersts = ['books, hi-tech', 'cinema, geek', 'travel, music', 'run']
        for i, interest in enumerate(intersts, start=0):
            redis_store.set('i:%s' % i, '["%s"]' % interest, 60)

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = Store(RedisStore())
        self.redis_start()

    @cases([
        {"phone": "79175002040", "email": "fake_email@mail.ru"},
        {"phone": 79175002040, "email": "fake_email@mail.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "fake_email@mail.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.redis_base.flushall()

        self.set_valid_auth(request)
        response, code = self.get_response(request)
        key = self.get_key(arguments)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(str(response['score']), self.redis_base.get(key))

    @cases([
        {"phone": "79175002040", "email": "fake_email@mail.ru", "score": 1.0},
        {"phone": 79175002040, "email": "fake_email@mail.ru", "score": 1.0},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b", "score": 1.0},
        {"gender": 0, "birthday": "01.01.2000", "score": 1.5},
        {"gender": 2, "birthday": "01.01.2000", "score": 1.0},
        {"first_name": "a", "last_name": "b", "score": 1.5},
        {"phone": "79175002040", "email": "fake_email@mail.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b", "score": 1.0},
    ])
    def test_cache_score(self, arguments):
        score = arguments.pop("score")
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.redis_base.flushall()
        key = self.get_key(arguments)
        self.redis_base.set(key, score)
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(score, response["score"])

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        self.redis_base.flushall()
        self.set_interests(self.redis_base)
        response, code = self.get_response(request)

        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        for i in arguments['client_ids']:
            self.assertEqual(response[str(i)], json.loads(self.redis_base.get('i:%s' % i)))


if __name__ == "__main__":
    unittest.main()
