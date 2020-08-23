import unittest
import functools
import datetime
import sys
import os

sys.path.append(os.path.join(os.getcwd(), ''))
import api
from tests.cases import cases


class TestCharField(unittest.TestCase):

    @cases(['name', ''])
    def test_char_field_valid_value(self, value):
        self.assertEqual(value, api.CharField().valid_value(value))
        self.assertIsInstance(api.CharField().valid_value(value), basestring)

    @cases([{},['89621234586'], None, set()])
    def test_invalid_char_field(self, value):
        with self.assertRaises(api.ValidationError):
            api.CharField().valid_value(value)


class TestArgumentsField(unittest.TestCase):

    @cases([{}, {'login': 'login'}])
    def test_arguments_valid_value(self, value):
        self.assertDictEqual(value, api.ArgumentsField().valid_value(value))

    @cases([[], ['login']])
    def test_invalid_type_arguments_value(self, value):
        with self.assertRaises(api.ValidationError):
            api.ArgumentsField().valid_value(value)


class TestEmailField(unittest.TestCase):

    @cases(['name@mail.ru', 'email@inbox.ru'])
    def test_email_valid_value(self, value):
        self.assertEqual(value, api.EmailField().valid_value(value))
        self.assertIsInstance(api.EmailField().valid_value(value), basestring)

    @cases(['name@mailru', 'email@inbox@ru', 'email.ru', ''])
    def test_invalid_email(self, value):
        with self.assertRaises(api.ValidationError):
            api.EmailField().valid_value(value)

    @cases([123456789, None, {}, [], set()])
    def test_invalid_type_email(self, value):
        with self.assertRaises(api.ValidationError):
            api.EmailField().valid_value(value)


class TestPhoneField(unittest.TestCase):

    @cases(['79991234567', 79991234567, 79991234576])
    def test_valid_phone_number(self, value):
        self.assertEqual(value, api.PhoneField().valid_value(value))
        self.assertIsInstance(api.PhoneField().valid_value(value), (basestring, int))

    @cases(['89991234567', 99991234567, '+79661234567', 'phone'])
    def test_invalid_phone_number(self, value):
        with self.assertRaises(api.ValidationError):
            api.PhoneField().valid_value(value)

    @cases([{},['89621234586'], None, set()])
    def test_invalid_type_phone_number(self, value):
        with self.assertRaises(api.ValidationError):
            api.PhoneField().valid_value(value)


class TestDateField(unittest.TestCase):

    @cases(['18.06.2010', '18.06.1800'])
    def test_valid_date(self, value):
        self.assertIsInstance(api.DateField().valid_value(value), datetime.datetime)

    @cases(['29.02.2011', '18.1800', '02.188.1999', '01,02,2010', '01/02/2010','str', '26 july 1929'])
    def test_invalid_date(self, value):
        with self.assertRaises(api.ValidationError):
            api.DateField().valid_value(value)


class TestBirthDayField(unittest.TestCase):

    @cases(['18.06.2010', '18.06.1960',])
    def test_valid_birthdate(self, value):
        self.assertIsInstance(api.DateField().valid_value(value), datetime.datetime)

    @cases(['29.02.2011', '18.1800', '02.188.1999', '01,02,2010', '01/02/2010','str', '26 july 1929'])
    def test_invalid_birthdate(self, value):
        with self.assertRaises(api.ValidationError):
            api.DateField().valid_value(value)

    @cases(['18.06.1800', '18.06.1900'])
    def test_invalid_limit_birthdate(self, value):
        with self.assertRaises(api.ValidationError):
            api.BirthDayField().valid_value(value)


class TestGenderField(unittest.TestCase):

    @cases([0, 1, 2])
    def test_valid_gender(self, value):
        self.assertEqual(api.GENDERS[value], api.GenderField().valid_value(value))
        self.assertTrue(api.GenderField().valid_value(value))

    @cases([-1, 3, 4])
    def test_invalid_gender(self, value):
        with self.assertRaises(api.ValidationError):
            api.GenderField().valid_value(value)

    @cases(['-1', '3', 'male'])
    def test_invalid_type_gender(self, value):
        with self.assertRaises(api.ValidationError):
            api.GenderField().valid_value(value)


class TestClientIDsField(unittest.TestCase):

    @cases([[1, 2, 3], [0], [3, 2, 1]])
    def test_valid_client_fields(self, value):
        self.assertListEqual(value, api.ClientIDsField().valid_value(value))

    @cases(['1', None])
    def test_invalid_type_client_fields(self, value):
        with self.assertRaises(api.ValidationError):
            api.ClientIDsField().valid_value(value)

    @cases([[1, 2, '3'], [None]])
    def test_invalid_client_fields(self, value):
        with self.assertRaises(api.ValidationError):
            api.ClientIDsField().valid_value(value)


if __name__ == "__main__":
    unittest.main()
