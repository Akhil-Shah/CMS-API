# Importing Library
from flask import Flask, request
from flask_restplus import Api, Resource, fields

import jwt

# Initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'keep_this_secret'

authorizations = {
    'token' : {
        'type' : 'apiKey',
        'in' : 'header',
        'name' : 'JWT-Token'
    }
}

api = Api(app,authorizations=authorizations)

# Defining the models
auth = api.model('auth',{
    'username':fields.String(required=True),
    'password':fields.String(required=True),
})

# Temporary Data Structures (Should be replaced by a Database later)
authors = [{'username':'Initial','password':'1234'}]

# Decorator Functions
def check_token(func):
    def wrapper(*args, **kwargs):

        try:
            token = request.headers['JWT-Token']
        except:
            return {"Error":"Token Missing"}

        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return {"Error":"Invalid Token"}

        return func(*args, **kwargs)

    return wrapper

# Routes
@api.route('/register')
class RegisterUser(Resource):

    @api.expect(auth)
    def post(self):
        username = api.payload['username']
        password = api.payload['password']
        
        authors.append({
            'username':username,
            'password':password,
        })

        return {"status":"New Author Added","authors":authors}

@api.route('/login')
class LoginUser(Resource):

    @api.expect(auth)
    def post(self):
        username = api.payload['username']
        password = api.payload['password']

        for each_user in authors:
            if each_user['username'] == username and each_user['password'] == password:
                token = jwt.encode({'username':username, 'password':password}, app.config['SECRET_KEY'], algorithm='HS256')
                return {"token":token.decode('UTF-8')}

@api.route('/author')
class AuthorContent(Resource):

    @api.doc(security='token')
    @check_token
    def get(self):
        return {"Made":"It"}

# Run API
if __name__ == '__main__':
    app.run(debug=True)