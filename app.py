from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from waitress import serve
import requests
import time
# import pyttsx3
from huggingface_hub import InferenceClient
import json
from dotenv import load_dotenv
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# app.app_context().push()
class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"

# Initialize the database
@app.route('/init_db')
def init_db():
    try:
        with app.app_context():
            db.create_all()
            print("Tables created!")
            return "<h1>Tables created successfully!</h1>", 200
    except Exception as e:
        return f"Error creating Tables: {str(e)}", 500


def call_chatBot(inference_client: InferenceClient, prompt: str):
    response = inference_client.post(
        json={
            "inputs": prompt,
            "parameters": {"max_new_tokens": 1000},
            "task": "text-generation",
        },
    )
    return json.loads(response.decode())[0]["generated_text"]
@app.route('/myfun', methods=['GET','POST'])
def index():
    if request.method == "POST":
        query = request.form['query']
        # lastname = request.form['lastname']
        print(query)
        # output = query
        if len(query.strip()) > 0:  
            try:
                response = take_cmd(query)
                return jsonify({'output':response})
            except Exception as e:
                print("The error is: ", str(e))
                return jsonify({'output': str(e)})
        else:
            return jsonify({'output':""})
        return jsonify({'error' : 'Error!'})
    return render_template('weather.html')

def take_cmd(query):
    a1 = ["hello", "namaskar", "namaste", "namskar" , "namste", "salam"]
    a2 = ["who r u", "who r u?" , "w r u", "who are you", "who are you?"]
    response = ""
    if any(x in query.lower() for x in a1) or query.lower() == "hi":
        # print(query)
        response = "Hello! I'm DeltaAI, How can I assist you today?"
        time.sleep(2)   
    elif any(x in query.lower() for x in a2):
        response ="I'm DeltaAI, your friendly AI assistant! I can help with answering questions, brainstorming ideas, learning new topics, writing, coding, and much more. What's on your mind?" 
        time.sleep(2)  
    elif "play" in query.lower():     
        print('Playing on Youtube....')  
        topic = query.lower().replace('play ', '')
        response = playonyt(topic)  
    else:
        # import os
        load_dotenv() # Load variables from .env file
        api_key = os.getenv('HF_TOKEN')
        model_1 = os.getenv('MODEL_1') 
        os.environ["HF_TOKEN"] = api_key
        repo_id = model_1
        My_client = InferenceClient(model=repo_id, timeout=120,)
        response = call_chatBot(My_client, query)
    return response

def playonyt(topic):
    # """Will play video on following topic, takes about 10 to 15 seconds to load"""
    url = 'https://www.youtube.com/results?q=' + topic
    print(url)
    count = 0
    cont = requests.get(url)
    data = str(cont.content)
    lst = data.split('"')
    for i in lst:
        count+=1
        if i == 'WEB_PAGE_TYPE_WATCH':
            break
    if lst[count-5] == "/results":
        raise Exception("No video found.")
    # web.open("https://www.youtube.com"+lst[count-5])
    return "https://www.youtube.com"+lst[count-5]

def GetWeather(city_name):    
    load_dotenv() # Load variables from .env file
    API_Key = os.getenv('API_Key') 
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_Key}'
    response = requests.get(url)
    return response

@app.route('/update_label', methods=['POST'])
def update_label():
    value = request.form.get('value')
    # Process the received value here (e.g., store it in a database)
    print("Received value:", value)
    return 'OK'

@app.route("/weather")
def weather():
    # take_text_cmd("Play National Anthem")
    city_name = "Nagpur"
    response = GetWeather(city_name)
    if response.status_code == 200:
        api_data = response.json()
        # print(api_data)
        temp_city = ((api_data['main']['temp']) - 273.15)
        temp_feels = ((api_data['main']['feels_like']) - 273.15)
        weather_desc = api_data['weather'][0]['description']
        hmdt = api_data['main']['humidity']
        wind_spd = api_data['wind']['speed']
        visibility = ((api_data['visibility']) / 1000)
        pressure = api_data['main']['pressure']
        clouds = api_data['clouds']['all']
        import pytz
        india_timezone = pytz.timezone('Asia/Kolkata')
        date_time = datetime.now(india_timezone).strftime("%d %b %Y | %I:%M:%S %p")
        
    return render_template('weather.html',temp_city=temp_city,city_name=city_name,
                           date_time=date_time,temp_feels=temp_feels,weather_desc=weather_desc,
                           hmdt=hmdt,wind_spd=wind_spd)

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method=='POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo(title=title, desc=desc) # Add data
        db.session.add(todo)
        db.session.commit()
        
    allTodo = Todo.query.all() 
    return render_template('index.html', allTodo=allTodo)

@app.route('/show')
def products():
    allTodo = Todo.query.all()
    print(allTodo)
    return 'this is products page'

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    if request.method=='POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo.query.filter_by(sno=sno).first()
        todo.title = title
        todo.desc = desc
        db.session.add(todo)
        db.session.commit()
        return redirect("/")
        
    todo = Todo.query.filter_by(sno=sno).first()
    return render_template('update.html', todo=todo)

@app.route('/delete/<int:sno>')
def delete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect("/")

# from model import predictDisease
# predictions = predictDisease("itching,skin_rash,nodal_skin_eruptions")
# predictions = predictDisease("Itching,Skin Rash,Nodal Skin Eruptions") # >>Fungal infection
# predictions = predictDisease("Continuous Sneezing,Shivering,Chills") # >>Allergy
# predictions = predictDisease("Shivering,Continuous Sneezing,Chills") # >>Allergy

# rf_prediction = predictions['rf_model_prediction']
# nb_prediction = predictions['naive_bayes_prediction']
# svm_prediction = predictions['svm_model_prediction']
# final_prediction = predictions['final_prediction']
# print ("-------------------------------------------------------------")
              
# print("RandomForest Prediction  :", rf_prediction)
# print("Gaussian_NB Prediction   :", nb_prediction)
# print("SVM Prediction           :", svm_prediction)
# print ("-------------------------------------------------------------")
# print("Final Prediction         :", final_prediction)
# print ("-------------------------------------------------------------")

if __name__ == "__main__":
    # app.debug = True
    # app.run(host="0.0.0.0", port=8000)
    serve(app, host="0.0.0.0", port=8000)
    
# CSS3 Loading animations 
# https://codepen.io/Manoz/pen/kyWvQw