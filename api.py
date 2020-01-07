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
auth_model = api.model('auth',{
    'username':fields.String(required=True),
    'password':fields.String(required=True),
})

content_model = api.model('content',{
    'title':fields.String(required=True,),
    'body':fields.String(required=True)
    #'summary':fields.String(required=True),
    #'document':fields.String(required=True),
    #'category':fields.String(required=True),
})

# Temporary Data Structures (Should be replaced by a Database later)
authors = [{'username':'Initial','password':'1234'}]
content = {}

# Global Variables
current_user = ''

# Decorator Functions
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

# Routes
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

        return {"status":"New Author Added","authors":authors}

@api.route('/login')
class LoginUser(Resource):

    @api.expect(auth_model)
    def post(self):
        username = api.payload['username']
        password = api.payload['password']

        for each_user in authors:
            if each_user['username'] == username and each_user['password'] == password:
                token = jwt.encode({'username':username, 'password':password}, app.config['SECRET_KEY'], algorithm='HS256')
                return {"token":token.decode('UTF-8')}

@api.route('/content')
class CreateContent(Resource):

    @api.expect(content_model)
    @api.doc(security='token')
    @check_token
    def post(self):

        if current_user not in content.keys():
            content[current_user] = [
                {
                    'title':api.payload['title'],
                    'body':api.payload['body']
                }
            ]
        else:
            content[current_user].append({
                'title':api.payload['title'],
                'body':api.payload['body']
            })
            
        return {"Success":"Content Added"}

@api.route('/content/<int:content_id>')
class ContentOperations(Resource):

    @api.doc(security='token')
    @check_token
    def get(self,content_id):
        return content[current_user][content_id-1]

    @api.expect(content_model)
    @api.doc(security='token')
    @check_token
    def put(self,content_id):
        content[current_user][content_id-1] = {
            'title':api.payload['title'],
            'body':api.payload['body']
        }

        return {"Success":"Content Updated"}

    @api.doc(security='token')
    @check_token
    def delete(self,content_id):
        del content[current_user][content_id-1]

        return {"Success":"Content Deleted"}
        

    



# Run API
if __name__ == '__main__':
    app.run(debug=True)