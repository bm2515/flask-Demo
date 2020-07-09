from flask import Flask, redirect, url_for, render_template, request, jsonify, abort, Response, json, request
from flask_api import status
from flask_inputs import Inputs
from cerberus import Validator
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
import json

#A Flask REST API Demo which records and retrieves user's daily fitness information
#How to Use Flask REST API:
#Step 1: Register a new user with the system by going to http://0.0.0.0:5000/register and entering user general information
#Step 2: Add Fitness Data by going to http://0.0.0.0:5000/users/username/add and entering user fitness information
#Step 3: Retrieve All User Fitness records by going to http://0.0.0.0:5000/users/username/data


#Credentials for DataBase connection
DBUSER = 'postgres'
DBPASS = 'test123'
DBHOST = 'localhost'
DBPORT = '5432'
DBNAME = 'SIHA_postgres'

#Initialization of Flask app
app = Flask(__name__)

#Connecting Flask App with POSTGRES DataBase using abovementioned DataBase credentials
app.config['JSON_SORT_KEYS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://{user}:{password}@{host}:{port}/{db}'.format(
        user=DBUSER,
        password=DBPASS,
        host=DBHOST,
        port=DBPORT,
        db=DBNAME)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Defining DataBase Instance
db = SQLAlchemy(app)

#Defining our first DataBase Table which records basic health information of the user
class User(db.Model):

    id = db.Column(db.Integer, primary_key = True)

    username = db.Column(db.String(20), unique=True, nullable=False)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    age = db.Column(db.String(50))
    sex = db.Column(db.String(50))
    height = db.Column(db.String(50))
    weight = db.Column(db.String(50))
    diabetes = db.Column(db.String(50))
    datecreated = db.Column(db.DateTime, default= datetime.now)
    
    fitness = db.relationship('Fitness', backref= 'user', lazy = True)

    #Defining User Table Initilization Function
    def __init__(self, username, firstname, lastname, age, sex, height, weight, diabetes):
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.age = age
        self.sex = sex
        self.height = height
        self.weight = weight
        self.diabetes = diabetes


#Defining our first DataBase Table which records daily fitness information of the user
class Fitness(db.Model):

    id = db.Column(db.Integer, primary_key = True)

    steps = db.Column(db.String(50))
    calories = db.Column(db.String(50))
    datecreated = db.Column(db.DateTime, default= datetime.now)

    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    #Defining Fitness Table Initilization Function
    def __init__(self, steps, calories, userid):

        self.steps = steps
        self.calories = calories
        self.userid = userid

#Define Schema for user general information

user_schema = {'username': {'type': 'string', 'required': True}, 
'firstname': {'type': 'string', 'required': True},
'lastname': {'type': 'string', 'required': True},
'age': {'type': 'string', 'required': True},
'sex': {'type': 'string', 'required': True},
'height': {'type': 'string', 'required': True},
'weight': {'type': 'string', 'required': True}, 
'diabetes': {'type': 'string', 'required': True}}


#Define Schema for User Fitness Information
fitness_schema = {'steps': {'type': 'string', 'required': True}, 
'calories': {'type': 'string', 'required': True}}



#API End Point to Register a new user to the System
@app.route("/users/register", methods=["POST"])
def add_user():

    #Validate POST Request Body is NON-EMPTY
    if (request.data):

        #Validate Content-Type for POST Request Body 
        if request.headers['Content-Type'] == 'application/json':
            
            #Get JSON POST Body
            requestdata = request.get_json()

            #Create an instance, v to validate data entry and type with user_schema
            v = Validator(user_schema)
            
            #Validate Data Entries for POST Request Body With Corresponding Defined Schema
            if v.validate(requestdata):

                #Retrieve newly entered User Information 
                username = requestdata["username"]
                firstname = requestdata["firstname"]
                lastname = requestdata["lastname"]
                age = requestdata["age"]
                sex = requestdata["sex"]
                height = requestdata["height"]
                weight = requestdata["weight"]
                diabetes = requestdata["diabetes"]

                #Create a user instance and add it to the DataBase
                user = User(username, firstname, lastname, age, sex, height, weight, diabetes)
                db.session.add(user)
                db.session.commit()

                return jsonify(requestdata)

            else:
                return Response("{'message':'Incorrect Data Field/Type Entry in the system. Please review User Schema'}", status=403)

        else:
            return Response("{'message':'Incorrect Content Type for post body request. Please enter data in JSON format'}", status=403)

    else:
        return Response("{'message':'Empty POST Request Body. Please review User Schema and enter data in JSON format'}", status=400)  



#API END Point to add new user Fitness information to the databse
@app.route("/users/<usr>/add", methods=["POST"])
def add_user_data(usr):
    
    #Validate POST Request Body is NON-EMPTY
    if (request.data):

        #Validate Content-Type for POST Request Body 
        if request.headers['Content-Type'] == 'application/json':

            #Get POST Request BODY
            requestdata = request.get_json()

            #Create an instance, v to validate newly entered fitness data with fitness_schema
            v = Validator(fitness_schema)
            
            #Validate Data Entries for POST Request Body With Defined Schema
            if v.validate(requestdata):

                #Retrieve newly entered user's fitness information
                steps = requestdata['steps']
                calories = requestdata['calories']

                #Retrieve user instance from the DataBase
                user = User.query.filter_by(username=usr).first()

                #Validate Username Exists In The DataBase
                if (user != None):

                    userid = user.id
                    
                    #Create a User Fitness Instance and add it to the DataBase
                    fitnessdata = Fitness(steps, calories, userid)
                    db.session.add(fitnessdata)
                    db.session.commit()

                    return jsonify(requestdata)
                
                else:
                    return Response("{'message':'Username entered in URL is not registered with the system. Please proceed to http://0.0.0.0:5000/users/register to add new user'}", status=404)

            else:
                return Response("{'message':'Incorrect Data Field/Type Entry in the system. Please Review User Fitness Schema'}", status=403)

        else:
            return Response("{'message':'Incorrect Content Type for post body request. Please enter data in JSON format'}", status=403)

    else:
        return Response("{'message':'Empty POST Request Body. Please Review User Fitness Schema and enter data in JSON format'}", status=400)        


#API End Point to retrieve User's all fitness data
@app.route("/users/<usr>/data", methods=["GET"])
def get_user_data(usr):

    OUTPUT = []

    user = User.query.filter_by(username=usr).first()

    #Validate Username Exists In The DataBase
    if (user != None):

        #Retrieve all user Fitness Records
        userdata = Fitness.query.filter_by(userid=user.id).all()
        
        #Append each fitness record to the OUTPUT
        for user in userdata:

            #Create an instance of fitness record to be displayed
            data = {
                    "steps": user.steps,
                    "calories": user.calories,
                    "datecreated": user.datecreated
            }

            OUTPUT.append(data)

        return jsonify(OUTPUT)
    
    else:
        return Response("{'message':'Username entered in URL is not registered with the system. Please proceed to http://0.0.0.0:5000/users/register to add new user'}", status=404)


#API End Point to Display User Credentials
@app.route("/users/<usr>", methods=["GET"])
def get_user (usr):

    user = User.query.filter_by(username=usr).first()

    #Validate Username Exists In The DataBase
    if (user != None):

        #Retrieve all user information
        firstname = user.firstname
        lastname = user.lastname
        age = user.age
        sex = user.sex
        height = user.height
        weight = user.weight
        diabetes = user.diabetes
        datecreated = user.datecreated

        #Return User Information to the User
        return jsonify({"firstname": firstname,
                "lastname": lastname,
                "age": age,
                "sex": sex,
                "height": height,
                "weight": weight,
                "diabetes": diabetes,
                "datecreated": datecreated
                })

    
    else:
        return Response("{'message':'The username present in URL is not registered with the system. Please proceed to http://0.0.0.0:5000/users/register to add new user'}", status=404)
	    

#RUN THE APP
if __name__ == '__main__':
   
    app.run(debug=True, host='0.0.0.0')