from flask import Flask, render_template, request, url_for, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import dotenv_values
config = dotenv_values(".env")
app = Flask(__name__)
print(f"config: {config}")
# client = MongoClient('localhost', 27017)

# db = client.flask_db
# todos = db.todos

# @app.route('/', methods=('GET', 'POST'))
# def index():
#     return render_template('index.html')

app.mongodb_client = MongoClient(config["ATLAS_URI"])
# app.database = app.mongodb_client[config["DB_NAME"]]
print("Connected to the MongoDB database!")
db = app.mongodb_client.flask_db
todos = db.todos

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method=='POST':
        content = request.form['content']
        degree = request.form['degree']
        todos.insert_one({'content': content, 'degree': degree})
        return redirect(url_for('index'))

    all_todos = todos.find()
    return render_template('index.html', todos=all_todos)


@app.post('/<id>/delete/')
def delete(id):
    todos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))


if __name__ == '__main__':
    # app.mongodb_client = MongoClient(config["ATLAS_URI"])
    # app.database = app.mongodb_client[config["DB_NAME"]]
    # print("Connected to the MongoDB database!")
    app.run(host='0.0.0.0', port=5011, debug=True)