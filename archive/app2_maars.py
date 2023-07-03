from flask import Flask, render_template, request, url_for, redirect, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import dotenv_values
import pandas as pd
from flask import Flask, request, jsonify
import requests

from flask_mqtt import Mqtt
import pandas as pd

## for connecting local mongodb
config = dotenv_values(".env")
app = Flask(__name__)

print(f"config: {config}")
# client = MongoClient('localhost', 27017)
client = MongoClient('mongodb+srv://user2:password123$$$@cluster0.wz9ds7q.mongodb.net/?retryWrites=true&w=majority', 27017)

db = client.flask_db
todos = db.todos2


latest_payload = {}

app.config['MQTT_BROKER_URL'] = 'broker.emqx.io'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your server supports TLS, set it True
# topic = '/flask/mqtt'
topic = 'cs462/feeds/rx'

mqtt_client = Mqtt(app)
import pandas as pd
timeAppStarted = pd.Timestamp.now()
global lastMongodbUpdate
global lastTelegramUpdate
lastMongodbUpdate =  pd.Timestamp.now()
lastTelegramUpdate = pd.Timestamp.now()

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print('Connected successfully')
       mqtt_client.subscribe(topic) # subscribe topic
   else:
       print('Bad connection. Code:', rc)

def format_data(msg):
    
    if "," in msg:
        uv, temp, humidity = msg.split(",")[:3]
    else:
        uv, temp, humidity = 0.06000, 23.00, 59.00

    import time
    
    return {
       "uv":uv,
       "humidity": humidity,
       "temperature": temp,
        "timestamp":pd.Timestamp.now()
   }

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    print("nnn:", message.payload.decode())
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
        )
#    # data to insert in future:
    formatted_data = format_data(message.payload.decode())

    import time
    if float(formatted_data['uv']) > 0:
        sendTgMessage("Please dont stay outside for too long, the current uv rating is " + formatted_data['uv'])

    global lastMongodbUpdate
    mongodelta = pd.Timestamp.now().to_pydatetime() - lastMongodbUpdate.to_pydatetime()
    print(f"time since last sent mongodb message : {mongodelta.seconds}")
    x = ""
    # only insert every 5 minutes - rate limitting on our side:
    if mongodelta.seconds / 60 > 1:
        x = todos.insert_one(formatted_data)
        x = str(x.inserted_id)
        lastMongodbUpdate = pd.Timestamp.now()

    print(f'Received message on topic: {message.topic} with payload: {data}  ' + x)

    global latest_payload 
    latest_payload = format_data(data["payload"])


@app.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.get_json()
   publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
   return jsonify({'code': publish_result[0]})

@app.route('/i', methods=('GET', 'POST'))
def index2():
    return render_template('dashboard.html')

@app.route('/c', methods=('GET', 'POST'))
def indexc():
    return render_template('dashboard_timeseries.html')

@app.route('/c2', methods=('GET', 'POST'))
def indexc2():
    return render_template('dashboard_timeseries_2.html')

@app.route('/h', methods=('GET', 'POST'))
def index4():
    return render_template('dashboard2.html')


@app.route('/o', methods=('GET', 'POST'))
def index3():
    return render_template('dashboardoriginal.html', days=["Monday", "Tues"])


import paho.mqtt.client as mqtt
# import paho.mqtt.client as mqtt
import time


# MQTT client object
mqttc = None

# # Topic to subscribe to. 
# # ***CHANGE THIS TO SOMETHING UNIQUE***
# TOPIC = "iot-mrloh"


# # Handles an MQTT client connect event
# # This function is called once, just after the mqtt client is connected to the server.
# def handle_mqtt_connack(client, userdata, flags, rc) -> None:
#     print(f"MQTT broker said: {mqtt.connack_string(rc)}")
#     if rc == 0:
#         client.is_connected = True

#     # Subscribing in on_connect() means that if we lose the connection and
#     # reconnect then subscriptions will be renewed.
#     client.subscribe(f"{TOPIC}")
#     print(f"Subscribed to: {TOPIC}")
#     print(f"Publish something to {TOPIC} and the messages will appear here.")


# # Handles an incoming message from the MQTT broker.
# def handle_mqtt_message(client, userdata, msg) -> None:
#     print(f"received msg | topic: {msg.topic} | payload: {msg.payload.decode('utf8')}")



# @app.route('/data2')
# def getDataUV():

    
@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method=='POST':
        content = request.form['content']
        degree = request.form['degree']
        todos.insert_one({'content': content, 'degree': degree})
        return redirect(url_for('index'))
    return render_template('two.html', days=["Monday", "Tues"])


# @app.route('/data')
# def getData():
#     df = pd.read_csv("data_measurements_2023-02-25T08_50_26.614Z.csv")
#     print(df)
#     gp_df = df.groupby("Time")
#     # gp_df.describe()
#     gp_df['c8y_SensorTagTemperature => Temperature'].agg(['max', 'min', 'count', 'median', 'mean'])
#     temp_data = gp_df['c8y_SensorTagTemperature => Temperature'].mean()
#     # make data
#     x = list(temp_data.index)
#     y = list(temp_data)
#     return jsonify({
#         "data": {
#         "x": x,
#         "y": y
#         }
#     })

@app.route('/data')
def getData():
    print(latest_payload)
    return jsonify(latest_payload)


def convert():
    db = client.flask_db
    todos = db.todos2

    x = todos.find()
        
    x = todos.find()
    data_pd = {}
    for data in x:
        data_pd[data['_id']] = [data['uv'], data['humidity'], data['temperature'], data['timestamp']]
    df = pd.DataFrame.from_dict(data_pd, orient='index', columns=['uv', 'humidity', 'temperature', 'timestamp'])
    # fill nas with average and convert all to numbers:
    # df.fillna(method="backfill")
    import numpy as np

    df['uv'] = df['uv'].apply(lambda x: float(x) if x != '' else np.nan)
    df['temperature'] = df['temperature'].apply(lambda x: float(x) if x != '' else np.nan)
    df['humidity'] = df['humidity'].apply(lambda x: float(x) if x != '' else np.nan)

    df = df.fillna(method="backfill")
    # print("any na values:", df['uv'].isna().sum())
    # sort by timestamp to get latest:
    df.sort_values(by='timestamp', inplace=True, ascending = False)
    df3 = df.groupby('timestamp', as_index=True)[['humidity', 'temperature']].mean()

    s30 = df3.temperature.resample("30s").mean()
    min1= df3.temperature.resample("1min").mean()
    d1 = df3.temperature.resample("1d").mean()

    s30 = s30.reset_index()
    min1 = min1.reset_index()
    d1 = d1.reset_index()

    # s30 = s30.to_json(orient='records')
    # min1 = min1.to_json(orient='records')
    # d1 = d1.to_json(orient='records')

    s30 = s30.sort_values("timestamp", ascending=False).iloc[:50]
    min1 = min1.sort_values("timestamp", ascending=False).iloc[:50]
    d1 = d1.sort_values("timestamp", ascending=False).iloc[:50]

    s30 = s30.fillna(method="backfill")
    min1 = min1.fillna(method="backfill")
    d1 = d1.fillna(method="backfill")

    s30 = s30.to_json(orient='records')[1:-1].replace('},{', '}A{')
    min1 = min1.to_json(orient='records')[1:-1].replace('},{', '}A{')
    d1 = d1.to_json(orient='records')[1:-1].replace('},{', '}A{')
    # print(s30)
    return s30, min1, d1

@app.route('/data2')
def getData_latest_day_week_month():
    print(latest_payload)

    data = convert()
    # print("got", data)
    return jsonify(data[0])

@app.route('/data_min')
def getData_latest_min():
    print(latest_payload)

    data = convert()
    # print("got", data)
    return jsonify(data[0])

@app.route('/data_hourly')
def getData_latest_hourly():
    print(latest_payload)

    data = convert()
    # print("data_hourly", data)
    return jsonify(data[1])



@app.route('/data_daily')
def getData_latest_daily():
    print(latest_payload)

    data = convert()
    # print("getData_latest_daily", data)
    return jsonify(data[2])




@app.post('/<id>/delete/')
def delete(id):
    todos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))

# import telebot
# import httpx
# import requests
# bot = telebot.TeleBot(config["b"])
# print(config["b"])

@app.get("/hook/<msg>")
def sendTgMessage(msg):
    """
    Sends the Message to telegram with the Telegram BOT API
    """
    global lastTelegramUpdate
    timedelta = pd.Timestamp.now().to_pydatetime() - lastTelegramUpdate.to_pydatetime()
    print(f"time since last sent telegram message : {timedelta.seconds}")
    # send alert another time after 1 minute has passed:
    if timedelta.seconds / 60 < 1:
        return "Done"
        
    lastTelegramUpdate = pd.Timestamp.now()
    TOKEN = "5937321827:AAEyB_WNnOpjf4GUz-hXrDGdtA7yaKZVKkE"
    CHAT_ID = 493366384  # Telegram Chat ID
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}"
    print(requests.get(url).json()) 


    print("completed")
    return "Done"


if __name__ == '__main__':
    app.mongodb_client = MongoClient(config["ATLAS_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to the MongoDB database!")
    app.run(host='0.0.0.0', port=5012, debug=True)
    