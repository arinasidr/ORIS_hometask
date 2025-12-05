from flask import Flask, render_template, redirect, request, url_for
import random

app = Flask(__name__)

data = [
        'если заблудился в лесу, иди домой',
        'никогда не сдавайтесь! а если будет сложно - сдавайтесь',
        'как говорил мой дед: я твой дед',
        'шаг влево, шаг вправо - два шага',
        'если закрыть глаза, становиться темно'
]

movie = [
        {"title": "Inception", "year": 2010, "rating": 8.8},
        {"title": "Dune", "year": 2021, "rating": 8.1},
        {"title": "Interstellar", "year": 2014, "rating": 8.6},
        {"title": "The Dark Knight", "year": 2008, "rating": 9.0},
        {"title": "Blade Runner 2049", "year": 2017, "rating": 8.0},
        {"title": "Parasite", "year": 2019, "rating": 8.6},
        {"title": "The Matrix", "year": 1999, "rating": 8.7},
        {"title": "Mad Max: Fury Road", "year": 2015, "rating": 8.1}
]

images_q = [
        {
            # "href": "https://iimg.su/i/K5OAzI",
            "src": "https://s3.iimg.su/s/05/gK5OAzIxvfvhbIIACI6b1KJJ8JEYnWHmmoFhPiGB.jpg"
        },
        {
            # "href": "https://iimg.su/i/iJk87D",
            "src": "https://s3.iimg.su/s/05/giJk87Dx90IQInNKSkWOK9VkqH1VcmtR3KIhbr8d.jpg"
        },
        {
            # "href": "https://iimg.su/i/BGx2EN",
            "src": "https://s3.iimg.su/s/05/gBGx2ENxUGmZWfRsGsJ2EnZFDW3nmdvD6QMRvDAy.jpg"
        },
        {
            # "href": "https://iimg.su/i/XlPt7T",
            "src": "https://s3.iimg.su/s/05/gXlPt7TxphDrQmBLUZvZZIyemjzTzDltAGcOBOF9.jpg"
        },
        {
            # "href": "https://iimg.su/i/W54LsG",
            "src": "https://s3.iimg.su/s/05/gW54LsGxXqL05i95RDEPZdwEkUtHaXQXIzMQIBTS.jpg"
        }
]

images = ['arina.jpg', 'arina2.jpg', 'diana.jpg', 'family.jpg', 'friends.jpg', 'friends2.jpg', 'love.jpg', 'nika.jpg',  'pashok.jpg', 'walk.jpg', 'pashadiana.jpg']

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/quote")
def quote():
    random_quote = random.choice(data)
    random_image = random.choice(images_q)
    return render_template("quote.html", quote=random_quote, image=random_image)

@app.get("/gallery")
def gallery():
    
    return render_template("gallery.html", images=images)

@app.get("/movies")
def movies():
    return render_template("movies.html", movie=movie)

@app.get("/calc")
def calc():
    result = None
    error = None

    if request.args:
        try:
            a = float(request.args.get("a"))
            b = float(request.args.get("b"))
            z = request.args.get("operation")

            if z == "+":
                result = a + b
            elif z == "-":
                result = a - b
            elif z == "*":
                result = a * b
            elif z == "/":
                if b == 0:
                    error = "нельзя делить на ноль блин"
                else:
                    result = a / b
        except:
            error = "ошибочки"
    a = request
    return render_template("calc.html", result = result, error = error)

@app.get("/convert")
def convert():
    result = None
    error = None

    if request.args:
        try:
            a = float(request.args.get("a"))
            f_or_c = request.args.get("res")
            
            if f_or_c == "c_to_f":
                f = a * 9/5 + 32
                result = f"{a} °C = {round(f, 2)} °F"
            elif f_or_c == "f_to_c":
                c = (a - 32) * 5/9
                result = f"{a} °F = {round(c, 2)} °C"
        except:
            error = "ошибочки"
    a = request
    return render_template("convert.html", result = result, error = error)

if __name__ == "__main__":
    app.run(debug=True)
