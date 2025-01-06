from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from waitress import serve
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()
class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"

#######Start Code Here ############
def GetWeather(city_name):    
    API_Key = "c819be33968724a0e04121b1d3795584"
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_Key}'
    response = requests.get(url)
    return response

@app.route("/weather")
def weather():
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
        date_time = datetime.now().strftime("%d %b %Y | %I:%M:%S %p")
        
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

if __name__ == "__main__":
    # db.create_all() 
    app.debug = True
    # app.run(host="0.0.0.0", port=8000)
    serve(app, host="0.0.0.0", port=8000)
    