from flask import Flask, render_template, request, url_for, redirect, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import dotenv_values
import pandas as pd
from flask import Flask, request, jsonify
import requests
# from flask_cors import CORS, cross_origin

from flask_mqtt import Mqtt
import pandas as pd
import numpy as np

import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

## for connecting local mongodb
config = dotenv_values(".env")
app = Flask(__name__)
# cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'

print(f"config: {config}")
# client = MongoClient('localhost', 27017)
client = MongoClient('mongodb+srv://user2:password123$$$@cluster0.wz9ds7q.mongodb.net/?retryWrites=true&w=majority', 27017)

db = client.flask_db
todos = db.todos4


latest_payload = {}

app.config['MQTT_BROKER_URL'] = 'broker.emqx.io'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your server supports TLS, set it True
topic = 'cs462/feeds/rx'
# in production:
# topic = 'cs462/feeds/rx/<device_no>'

# Last Will Configurations:
app.config['MQTT_LAST_WILL_TOPIC'] = topic
app.config['MQTT_LAST_WILL_MESSAGE'] = "Publisher unexpectedly disconnected"
app.config['MQTT_LAST_WILL_QOS'] = 1
app.config['MQTT_LAST_WILL_RETAIN'] = True


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

def calculate_apparent_temperature(temp, humidity):
    return temp + 0.348 * humidity - 0.7 * 1 + 0.7 * (136/11)-4.25

@app.route('/devicestatus')
def getDeviceStatus():
    
    return jsonify({
        "status": "connected" if connectionStatus else "disconnected"
    })

global connectionStatus
connectionStatus = True
def format_data(msg):
    global connectionStatus
    if "Publisher unexpectedly disconnected" in msg:
        connectionStatus = False
    else:
        connectionStatus = True
    if "," in msg:
        splitMsg = msg.split(",")
        if len(splitMsg) != 4:
            uv, temp, humidity = 0.06000, 23.00, 59.00
        else:
            uv, temp, humidity = msg.split(",")[:3]
            print(uv,temp,humidity)
            uv = float(uv)
            temp = float(temp)
            humidity = float(humidity)
            print(uv,temp,humidity)
    else:
        uv, temp, humidity = 0.06000, 23.00, 59.00

    import time
    

    # # current location obtained from mobile app:
    # import json
    # url = 'http://freegeoip.net/json/{}'.format(request.remote_addr)
    # r = requests.get(url)
    # j = json.loads(r.text)
    # city = j['city']

    return {
       "uv":uv,
       "humidity": humidity,
       "temperature": temp,
        "timestamp":pd.Timestamp.now(),
        "apparentTemperature" : calculate_apparent_temperature(temp, humidity)
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
    if 0 < float(formatted_data['uv']) < 2:
        uv_levels = str(formatted_data['uv'])
        # alert not activated when uv index too low
        sendTgMessage("Please dont stay outside for too long, the current uv rating is low with an index of " + uv_levels + ". It is a good idea to apply sunscreen with spf 15.")
    elif 2 <= float(formatted_data['uv']) < 4:
        uv_levels = str(formatted_data['uv'])
        print("moderateee:", uv_levels)
        sendTgMessage("Please dont stay outside for too long, the current uv rating is moderate with an index of " + uv_levels + ". It is a good idea to apply sunscreen with spf 30.")
    elif 4 <= float(formatted_data['uv']):
        uv_levels = str(formatted_data['uv'])
        sendTgMessage("Please dont stay outside for too long, the current uv rating is high with an index of " + uv_levels + ". It is a good idea to apply sunscreen with spf 50.")

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

"""
@app.route('/i', methods=('GET', 'POST'))
def index2():
    return render_template('dashboard.html')

@app.route('/c', methods=('GET', 'POST'))
def indexc():
    return render_template('dashboard_timeseries.html')

@app.route('/c2', methods=('GET', 'POST'))
def indexc2():
    return render_template('dashboard_timeseries_3.html')

@app.route('/h', methods=('GET', 'POST'))
def index4():
    return render_template('dashboard2.html')


@app.route('/o', methods=('GET', 'POST'))
def index3():
    return render_template('dashboardoriginal.html', days=["Monday", "Tues"])
"""

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
# @cross_origin()
def index():
    if request.method=='POST':
        content = request.form['content']
        degree = request.form['degree']
        todos.insert_one({'content': content, 'degree': degree})
        return redirect(url_for('index'))
    return render_template('dashboard.html', days=["Monday", "Tues"])

@app.route('/data')
def getData():
    print(latest_payload)
    return jsonify(latest_payload)

def predict_time_left_before_sunburn(df):
    print("CALLED TIME LEFT")
    add_0_3_uv = lambda uv: 3 * uv/3
    add_3_5_uv = lambda uv: 4 * uv/5
    add_6_7_uv = lambda uv: 6 * uv/7
    add_8_10_uv = lambda uv: 9 * uv/10
    add_11_uv = lambda uv: 18 * uv/11

    today_df = df[df['timestamp'].apply(lambda x: x.day == pd.Timestamp.now().day)]
    #today_df['time_from_now'] = df['time'] - (pd.Timestamp.now().time().hours * 3600 - pd.Timestamp.now().time().minute * 60 - pd.Timestamp.now().time.second)
    today_df = df[df['timestamp'].apply(lambda x: x.day == pd.Timestamp.now().day)]
    today_df = today_df.sort_values('timestamp', ascending=False)
    today_df['diff'] = today_df.diff()['time'].abs() / 60
    today_df['diff'] = today_df['diff'].fillna(0)
    today_df = today_df.sort_values('timestamp', ascending=True)
    
    is_sunburnt_total = 180 
    sunburn_val = 0 
    for row in today_df.iterrows():
        uv = row[1][0]
        diff = row[1][7] 
        if uv <= 3.5:
            sunburn_val += add_0_3_uv(uv) * diff 
        elif uv <= 5.5:
            sunburn_val += add_3_5_uv(uv) * diff 
        elif uv <= 7.5:
            sunburn_val += add_6_7_uv(uv) * diff 
        elif uv <= 10.5:
            sunburn_val += add_8_10_uv(uv) * diff 
        else:
            sunburn_val += add_11_uv(uv) * diff 

    if len(today_df) == 0:
        return 1,360

    curr_uv = today_df['uv'][-1]
    dist_to_sunburn = is_sunburnt_total - sunburn_val

    if dist_to_sunburn > 0:
        if curr_uv <= 3.5:
            val = add_0_3_uv(curr_uv)
            minutes_left = dist_to_sunburn / val 
            return 1, minutes_left
        elif curr_uv <= 5.5:
            val = add_3_5_uv(curr_uv)
            minutes_left = dist_to_sunburn / val 
            return 1, minutes_left
        elif curr_uv <= 7.5:
            val = add_6_7_uv(curr_uv)
            minutes_left = dist_to_sunburn / val 
            return 1, minutes_left
        elif curr_uv <= 10.5:
            val = add_8_10_uv(curr_uv)
            minutes_left = dist_to_sunburn / val 
            return 1, minutes_left
        else:
            val = add_11_uv(curr_uv)
            minutes_left = dist_to_sunburn / val 
            return 1, minutes_left
    else:
        return 0, sunburn_val // 18

def convert_to_datetime(val):
    hour = val // 3600 
    minute = (val % 3600) // 60
    second = val % 3600 % 60
    return datetime.time(int(hour), int(minute), int(second))

def predict_danger(df):
    ss = StandardScaler()
    X = ss.fit_transform(df[['time']])

    poly = PolynomialFeatures(2)
    X_poly = poly.fit_transform(X)

    logreg = LogisticRegression()
    logreg.fit(X_poly, df['is_danger'])

    times = np.array([x for x in range(0,3600*24,30)]).reshape(-1,1)
    times = ss.transform(times)
    times_poly = poly.transform(times)

    pred = logreg.predict_proba(times_poly)[:,1]

    times = ss.inverse_transform(times)
    # Adjust decision function
    c = datetime.datetime.now()
    percent = 1
    thresh = 1
    og = np.copy(pred)
    while percent > 0.4 and thresh > 0:
        pred = [
            pd.Timestamp(datetime.datetime(year=c.year, month=c.month, day=c.day, hour=convert_to_datetime(times[idx]).hour, 
            minute=convert_to_datetime(times[idx]).minute, second=convert_to_datetime(times[idx]).second))
            for idx in range(len(og)) if og[idx] > 0
        ]
        thresh -= 0.05
        percent = len(pred) / len(og) 
        print(percent, thresh)

    if thresh >= 1:
        print("EORR")

    my_dict = {
        'from':pred[0].strftime('%Y-%m-%d %X'),
        'to':pred[-1].strftime('%Y-%m-%d %X')
    }
    
    return jsonify(my_dict)

def is_danger(uv, appTemp):
    if uv > 8:
        return True 
    if appTemp > 60:
        return True
    return False

def get_resampled_df(df3, var):
    s30 = df3[var].resample("1min").mean()
    min1= df3[var].resample("1h").mean()
    d1 = df3[var].resample("1d").mean()

    s30 = s30.reset_index()
    min1 = min1.reset_index()
    d1 = d1.reset_index()


    # s30 = s30.to_json(orient='records')
    # min1 = min1.to_json(orient='records')
    # d1 = d1.to_json(orient='records')

    s30 = s30.sort_values(by="timestamp",ascending=False).iloc[:50]
    min1 = min1.sort_values(by="timestamp",ascending=False).iloc[:50]
    d1 = d1.sort_values(by="timestamp",ascending=False).iloc[:50]

    s30 = s30.fillna(method="backfill")
    min1 = min1.fillna(method="backfill")
    d1 = d1.fillna(method="backfill")

    s30 = s30.shift(periods=s30[var].isna().sum())
    s30['timestamp'] = pd.date_range(s30.iloc[-1]['timestamp'], freq='min', periods=min(len(s30), 50))
    s30['timestamp'] = s30['timestamp'].apply(lambda x: pd.Timestamp(x))

    min1 = min1.shift(periods=min1[var].isna().sum())
    min1['timestamp'] = pd.date_range(min1.iloc[-1]['timestamp'], freq='h', periods=min(len(min1), 50))
    min1['timestamp'] = min1['timestamp'].apply(lambda x: pd.Timestamp(x))

    d1 = d1.shift(periods=d1[var].isna().sum())
    d1['timestamp'] = pd.date_range(d1.iloc[-1]['timestamp'], freq='D', periods=min(len(d1), 50))
    d1['timestamp'] = d1['timestamp'].apply(lambda x: pd.Timestamp(x))

    s30['time'] = s30['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %X"))
    min1['time'] = min1['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %X"))
    d1['time'] = d1['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %X"))

    s30 = s30.to_json(orient='records')[1:-1].replace('},{', '}A{')
    min1 = min1.to_json(orient='records')[1:-1].replace('},{', '}A{')
    d1 = d1.to_json(orient='records')[1:-1].replace('},{', '}A{')
    return s30, min1, d1

def get_df():
    db = client.flask_db
    todos = db.todos4

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

    df['apparent_temperature'] = df['temperature'] + 0.348 * df['humidity'] - 0.7 * 1 + 0.7 * (136/11)-4.25
    # Change is_danger function to determine if user is in danger
    df['is_danger'] = df.apply(lambda row: is_danger(row['uv'], row['apparent_temperature']), axis = 1)

    df['time'] = df['timestamp'].apply(lambda x: x.time().hour * 3600 + x.time().minute * 60 + x.time().second)

    df = df.fillna(method="backfill")
    df.index = df.index.astype("str")

    # print("any na values:", df['uv'].isna().sum())
    # sort by timestamp to get latest:
    df.sort_values(by='timestamp', inplace=True, ascending = False)
    return df

def convert(var):
    df = get_df()
    df3 = df.groupby('timestamp', as_index=True).mean()

    s30T, min1T, d1T = get_resampled_df(df3, var)

    is_time, time_before_sunburn = predict_time_left_before_sunburn(df)
    my_dict = {0:-1,1:-1}
    my_dict[is_time] = time_before_sunburn
    #danger_range = predict_danger(df)
    return s30T, min1T, d1T, my_dict

@app.route('/data2')
def getData_latest_day_week_month():
    print(latest_payload)

    data = convert()
    # print("got", data)
    return jsonify(data[0])

@app.route('/alerts')
def getAlerts():
    alerts = db.alerts
    alerts_collected = []
    for i in alerts.find():
        alerts_collected.append({"user": i['user'], 'sensitivity': i['sensitivity'], 
                            'temperature': i['temperature'],
                            'uv': i['uv'],
                            'humidity': i['humidity'],
                            "id": i['id']})
    return jsonify(alerts_collected)

@app.route('/alertsdelete/<id>')
def deleteAlert(id):
    id = int(id)
    myquery = { "id": id }
    alerts = db.alerts
    done = alerts.delete_one(myquery)
    return "Done"

@app.route('/createalert', methods=['POST'])
def insertdata():
    data = request.get_json()
    alerts = db.alerts
    mydoc = alerts.find().sort("id", -1)
    lastId = 0
    for x in mydoc:
        lastId = x['id']
        break
    data['id'] = lastId + 1
    data['user'] = "user1"
    print("insertdata: ",data)
    x = alerts.insert_one(data)
    x = str(x.inserted_id)
    print(f"id generated for inserted data: {x}")
    return "done"


time_dict = {
    "min": 0,
    "hour": 1,
    "day":2
}

@app.route('/get-ml-data/<type>')
def getMLModel(type="danger_range"):
    df = get_df()
    if type == "danger_range":
        return predict_danger(df)
    return (0,0)

@app.route('/get-data/<time_step>/<type>')
def getResampledData(time_step="min", type="temperature"):
    if type in ["humidity","temperature","uv", "apprentTemperature"]:
        data = convert(type)
    else:
        return 
    
    try:
        time = time_dict[time_step]
    except KeyError:
        print("Not Found")
        time_step="min"
        type="temperature"

    print(data[3])
    
    return jsonify({0:data[time],1: data[3]})



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
    # In production: users would have to register their telegram id 
    # and it would be added to their account details in mongodb
    CHAT_ID = 493366384  # Telegram Chat ID - maars
    CHAT_ID2 = 5550112859
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}"
    url2 = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID2}&text={msg}"
    print(requests.get(url).json()) 
    print(requests.get(url2).json()) 


    print("completed")
    return "Done"


if __name__ == '__main__':
    app.mongodb_client = MongoClient(config["ATLAS_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to the MongoDB database!")
    app.run(host='0.0.0.0', port=5012, debug=True)
    