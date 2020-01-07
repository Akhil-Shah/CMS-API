# Importing Library
from flask import Flask, request
from flask_restplus import Api, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage

import jwt
import base64

# Initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'keep_this_secret' # Used in jwt

authorizations = {
    'token' : {
        'type' : 'apiKey',
        'in' : 'header',
        'name' : 'JWT-Token'
    }
}

api = Api(app,authorizations=authorizations)

# Defining the models
auth_model = api.model('auth',{
    'username':fields.String(required=True),
    'password':fields.String(required=True),
})

pagination_model = api.model('pagination',{
    'start':fields.Integer(required=True),
    'end':fields.Integer(required=True)
})

# Defining a Parser instead of Content Model (For handling documents)
parser = api.parser()
parser.add_argument('title', required=True)
parser.add_argument('body', required=True)
parser.add_argument('summary', required=True)
parser.add_argument('document', location='files',
                    type=FileStorage, required=True)
parser.add_argument('category', required=True)


# Temporary Data Structures (Should be replaced by a Database later)
authors = []
content = {}
admin = [{'username':'admin','password':'admin'}]

# Global Variables
current_user = ''

# Decorator Functions (JWT Authentication)
def check_token(func):
    def wrapper(*args, **kwargs):

        try:
            token = request.headers['JWT-Token']
        except:
            return {"Error":"Token Missing"}

        try:
            info = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            global current_user
            current_user = info['username']
        except:
            return {"Error":"Invalid Token"}

        return func(*args, **kwargs)

    return wrapper


def check_admin(func):
    def wrapper(*args, **kwargs):

        try:
            token = request.headers['JWT-Token']
        except:
            return {"Error":"Token Missing"}

        try:
            info = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            for each_admin in admin:
                if each_admin['username'] == info['username'] and each_admin['password'] == info['password']:
                    return func(*args, **kwargs)
        except:
            return {"Error":"Invalid Token"}

        return {"Error":"Not a Admin"}

    return wrapper

# Routes

# For Admin to view everybody's Content
@api.route('/admin')
class AdminControl(Resource):

    @api.doc(security='token')
    @check_admin
    def get(self):
        return content

# For Registering User
@api.route('/register')
class RegisterUser(Resource):

    @api.expect(auth_model)
    def post(self):
        username = api.payload['username']
        password = api.payload['password']
        
        authors.append({
            'username':username,
            'password':password,
        })

        return {"Status":"New Author Added"}

# For Login, returns a jwt token which is to be used
@api.route('/login')
class LoginUser(Resource):

    @api.expect(auth_model)
    def post(self):
        username = api.payload['username']
        password = api.payload['password']

        try:
            for each_admin in admin:
                if each_admin['username'] == username and each_admin['password'] == password:
                    token = jwt.encode({'username':username, 'password':password}, app.config['SECRET_KEY'], algorithm='HS256')
                    return {"token":token.decode('UTF-8')}

            for each_user in authors:
                if each_user['username'] == username and each_user['password'] == password:
                    token = jwt.encode({'username':username, 'password':password}, app.config['SECRET_KEY'], algorithm='HS256')
                    return {"token":token.decode('UTF-8')}

            return {"Error":"Account Does not Exist"}, 401

        except:
            return {"Error":"Account Does not Exist"}, 401

@api.route('/content')
class CreateContent(Resource):

    @api.expect(parser)
    @api.doc(security='token')
    @check_token
    def post(self):
        args = parser.parse_args()
    
        if current_user not in content.keys():
            content[current_user] = [
                {
                    'title':args['title'],
                    'body':args['body'],
                    'summary':args['summary'],
                    'document':base64.b64encode(args['document'].read()).decode('utf-8'),
                    'category':args['category']
                }
            ]
        else:
            content[current_user].append({
                'title':args['title'],
                'body':args['body'],
                'summary':args['summary'],
                'document':base64.b64encode(args['document'].read()).decode('utf-8'),
                'category':args['category']
            })
    
        return {"Success":"Content Added"}

@api.route('/content/<int:content_id>')
class ContentOperations(Resource):

    @api.doc(security='token')
    @check_token
    def get(self,content_id):

        try:
            return content[current_user][content_id-1]
        except:
            return {"Error":"Content Not Found"}, 400


    @api.expect(parser)
    @api.doc(security='token')
    @check_token
    def put(self,content_id):

        args = parser.parse_args()

        try:
            content[current_user][content_id-1] = {
                'title':args['title'],
                'body':args['body'],
                'summary':args['summary'],
                'document':base64.b64encode(args['document'].read()).decode('utf-8'),
                'category':args['category']
            }
        except:
            return {"Error":"Content Not Found"}, 400

        return {"Success":"Content Updated"}

    @api.doc(security='token')
    @check_token
    def delete(self,content_id):

        try:
            del content[current_user][content_id-1]
        except:
            return {"Error":"Content Not Found"}, 400

        return {"Success":"Content Deleted"}


@api.route('/pagination')
class Pagination(Resource):

    @api.expect(pagination_model)
    @api.doc(security='token')
    @check_token
    def post(self):

        start = api.payload['start']
        end = api.payload['end']

        try:
            return content[current_user][start-1:end]
        except:
            return {"Error":"Content Not Found"}, 400

# Run API
if __name__ == '__main__':
    app.run(debug=True)