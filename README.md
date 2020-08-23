### Python 2.7
### Scoring API
Validation system of requests to the HTTP API scoring service.
The user sends a valid JSON in a POST request of a certain format.
#### Request structure
```json
{
  "account": "<partner company name>",
  "login": "<user name>",
  "method": "<method name>",
  "token": "<authentication token>",
  "arguments": {<dictionary with arguments to the called method>}
}
```
Fields list:
* account - string, optionally, may be empty
* login - string may be empty
* method - string must be empty
* token - string must be empty
* arguments - the dictionary may be empty

#### Request structure
- {+ OK +}
```json
{"code": <code>, "response": {<response method>}}
```
- {- ERROR -}
```json
{"code": <code>, "error": {<message error>}}
```
### Metods
#### online_score.
Arguments list:
* phone - string or number, length 11, starts with 7, optionally, can be empty
* email - string containing @, optionally, may be empty
* first_name - string, optionally, may be empty
* last_name - string, optionally, may be empty
* birthday - date in DD.MM.YYYY format, from which no more than 70 years have passed, optionally, can be empty
* gender - the number 0, 1 or 2, optionally, may be empty

#### Request structure
- {+ OK +}
```json
{"score": <number>}
```
- {- ERROR -}
```json
{"code": 422, "error": "<message about which field is invalid>"}
```
```json
### Example
$ curl -X POST -H "Content-Type: application/json" -d
'{
   "account": "horns&hoofs",
   "login": "h&f",
   "method": "online_score",
   "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
   "arguments":
        {
        "phone": "79175002040",
        "email": "fake@mail.ru",
        "first_name": "Niels",
        "last_name": "Bohr",
        "birthday": "01.01.1990",
        "gender": 1
        }
}' http://127.0.0.1:8080/method/
```

#### clients_interests
Arguments list:
* client_ids - an array of numbers, certainly not empty
* date - date in DD.MM.YYYY format, optionally, may be empty

#### Request structure
- {+ OK +}
```json
{"client_id1": ["interest1", "interest2" ...], "client2": [...] ...}
```
- {- ERROR -}
```json
{"code": 422, "error": "<message about which field is invalid>"}
```
### Example
```json
$ curl -X POST -H "Content-Type: application/json" -d 
'{
   "account": "horns&hoofs",
   "login": "admin",
   "method": "clients_interests",
   "token": "d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f24091386050205c324687a0",
   "arguments": 
        {
        "client_ids": [1,2,3,4],
        "date": "20.07.2017"
        }
}' http://127.0.0.1:8080/method/
```
- {+ OK +}
```json
{"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4": ["cinema", "geek"]}}
```
### Tests

* python -m tests.unit.test_fields
* python -m tests.unit.test_store
* python -m tests.integration.test_api
* python -m tests.integration.test_store

### To run HTTP-server
* python -m api
# API-scoring
