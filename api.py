import abc
import json
import datetime
import logging
import hashlib
import uuid
import re
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from scoring import get_score, get_interests
from store import Store, RedisStore


SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request in test",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}

#************************************************FIELD******************************************************************

class ValidationError(Exception):
    pass


class Field(object):
    """Base class of request fields.

    Checks the validity of values for request fields.
    """

    __metaclass__= abc.ABCMeta

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.default = None

    def __get__(self, instance, owner):
        field_name = getattr(self, 'name')
        return instance.__dict__.get(field_name, self.default)

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        if not self.required and value is None:
            return
        if self.required and value is None:
            raise ValidationError('This field is required.')
        if not self.nullable and value in ('', {}, [], None):
            raise ValidationError('This field cannot be empty.')
        field_name = getattr(self, 'name')
        instance.__dict__[field_name] = self.valid_value(value)

    @abc.abstractmethod
    def valid_value(self, value):
        return


class CharField(Field):
    def valid_value(self, value):
        if not isinstance(value, basestring):
            raise ValidationError('The field must be of string type.')
        return value


class ArgumentsField(Field):
    def valid_value(self, value):
        if not isinstance(value, dict):
            raise ValidationError('The field must be a dictionary type.')
        return value


class EmailField(Field):
    def valid_value(self, value):
        if not isinstance(value, basestring):
            raise ValidationError('The field must be of string type.')
        if not re.match(r'[^@]+@[^@]+\.[^@]+', value):
            raise ValidationError('Email is not valid.')
        return value


class PhoneField(Field):
    def valid_value(self, value):
        if not isinstance(value, (basestring, int)):
            raise ValidationError('The field must be a string or integer type.')
        if not re.match(r'7\d{10}', str(value)):
            raise ValidationError('Telephone is not valid.')
        return value


class DateField(Field):
    def valid_value(self, value):
        try:
            return datetime.datetime.strptime(value, '%d.%m.%Y')
        except:
            raise ValidationError('Field has an invalid date format.')


class BirthDayField(DateField):
    def valid_value(self, value):
        value = super(BirthDayField, self).valid_value(value)
        limit_yars = 70
        if (datetime.datetime.now().year - value.year) > limit_yars:
            raise ValidationError(
                'Age can not be more than %s years.' % 
                (limit_yars))
        return value


class GenderField(Field):
    def valid_value(self, value):
        if not isinstance(value, int):
            raise ValidationError('The field must be an integer type (0, 1 or 2).')
        if not value in (UNKNOWN, MALE, FEMALE):
            raise ValidationError('The gender field must be 0, 1, or 2.')
        return GENDERS[value]


class ClientIDsField(Field):
    def valid_value(self, value):
        if not isinstance(value, list):
            raise ValidationError('The field must be a list of type.')
        if len(value) == 0 or not all([isinstance(elem, int) for elem in value]):
            raise ValidationError(
                'The field must not be an empty list of integer type elements.')
        return value

#***********************************************REQUEST*****************************************************************

class RequestMeta(type):
    """Metaclass for classes that would use validation.
    
    Sets proper labels to instances of `Field` class. Saves fields
    for validation to `declared_defs` attribute.
    """

    def __new__(cls, name, bases, attrs):
        request_class = super(RequestMeta, cls).__new__(cls, name, bases, attrs)
        request_class.declared_defs = {}
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, Field):
                attr_value.name = attr_name
                request_class.declared_defs[attr_name] = attr_value
        return request_class


class BaseRequest(object):
    """Base class that uses fields validation.
    """

    __metaclass__ = RequestMeta

    def __init__(self, arguments_fied):
        self.arguments_fied = arguments_fied
        self.default = None
        self.error_field = {}
    
    '''The method is used to validate fields.'''
    def valid_required_field(self):
        for field, obj in self.declared_defs.items():
            try:
                setattr(self, field, self.arguments_fied.get(field, self.default))
            except ValidationError, e:
                self.error_field[field] = e.args[0]


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    account = request.account.encode('utf-8') if request.account else ''
    login = request.login.encode('utf-8') if request.login else ''

    if request.is_admin:
        digest = hashlib.sha512(
            datetime.datetime.now().strftime("%Y%m%d%H") + 
            ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(account + login + SALT).hexdigest()

    if digest == request.token:
        return True
    return False


def online_score_progress(method_request, ctx, store):

    request = OnlineScoreRequest(method_request.arguments)
    request.valid_required_field()

    if request.error_field:
        return "<Invalid fields: %s>" % (request.error_field), INVALID_REQUEST

    ctx['has'] =  [field for field in request.arguments_fied.keys() if getattr(request, field)]
    if method_request.is_admin:
        return {"score": 42}, OK

    if request.phone and request.email or \
             request.first_name and request.last_name or \
             request.gender and request.birthday:
        response = {
            "score": get_score(
                store, request.phone,
                request.email, request.birthday,
                request.gender, request.first_name,
                request.last_name)}
        return response, OK
    else:
        invalid_field = [field for field in request.arguments_fied.keys() if not getattr(
            request, field)]
        return "<Invalid fields: %s>" % (invalid_field), INVALID_REQUEST


def clients_interests_progress(method_request, ctx, store):
    request = ClientsInterestsRequest(method_request.arguments)
    request.valid_required_field()

    if request.error_field:
        return "<Invalid fields: %s>" % (request.error_field), INVALID_REQUEST

    ctx['nclients'] = len(request.client_ids)
    response = {}
    for cid in request.client_ids:
        response.update({str(cid): get_interests(store, cid)})
    return response, OK


def method_handler(request, ctx, store):
    handler = {
        'online_score': online_score_progress,
        'clients_interests': clients_interests_progress,
    }

    method_request = MethodRequest(request['body'])
    method_request.valid_required_field()

    if method_request.error_field:
        return "<Invalid fields: %s>" % (method_request.error_field), INVALID_REQUEST

    if not check_auth(method_request):
        return None, FORBIDDEN

    if not method_request.method in handler:
        return None, FORBIDDEN

    response, code = handler[method_request.method](method_request, ctx, store)
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = Store(RedisStore())

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))

            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()