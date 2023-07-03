import time
import paho.mqtt.client as mqtt
from flask import Flask, render_template, request, url_for, redirect, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import dotenv_values
import pandas as pd
from flask import Flask, request, jsonify

from flask_mqtt import Mqtt


# for connecting local mongodb
config = dotenv_values(".env")
app = Flask(__name__)

print(f"config: {config}")
# client = MongoClient('localhost', 27017)
client = MongoClient(
    'mongodb+srv://user2:password123$$$@cluster0.wz9ds7q.mongodb.net/?retryWrites=true&w=majority', 27017)

db = client.flask_db
todos = db.todos


latest_payload = {}

app.config['MQTT_BROKER_URL'] = 'broker.emqx.io'
app.config['MQTT_BROKER_PORT'] = 1883
# Set this item when you need to verify username and password
app.config['MQTT_USERNAME'] = ''
# Set this item when you need to verify username and password
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
# If your server supports TLS, set it True
app.config['MQTT_TLS_ENABLED'] = False
# topic = '/flask/mqtt'
topic = 'cs462/feeds/rx'

mqtt_client = Mqtt(app)


@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        mqtt_client.subscribe(topic)  # subscribe topic
    else:
        print('Bad connection. Code:', rc)


def calculate_apparent_temperature(temp, humidity):
    return temp + 0.348 * humidity - 0.7 * 1 + 0.7 * (136/11)-4.25

def format_data(msg):
    print(msg)
    uv, temp, humidity = msg[:-1].split(",")
    import time
    import pandas as pd
    return {
        "uv": uv,
        "humidity": humidity,
        "temperature": temp,
        "timestamp": str(time.time()),
        "apparentTemperature" : calculate_apparent_temperature(temp, humidity)
    }


@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        data = dict(
            topic=message.topic,
            payload=message.payload.decode()
        )
#    # data to insert in future:
#    data = format_data(message)
        x = todos.insert_one(data)

        x = str(x.inserted_id)
        print('Received message on topic: {topic} with payload: {payload}  '.format(
            **data) + x)

        global latest_payload
        latest_payload = format_data(data["payload"])
    except:
        print("sad")


@app.route('/publish', methods=['POST'])
def publish_message():
    request_data = request.get_json()
    publish_result = mqtt_client.publish(
        request_data['topic'], request_data['msg'])
    return jsonify({'code': publish_result[0]})


# @app.route('/', methods=('GET', 'POST'))
# def index():
#     return render_template('index.html')

# to the internet mongodb version
# app.mongodb_client = MongoClient(config["ATLAS_URI"])
# # app.database = app.mongodb_client[config["DB_NAME"]]
# print("Connected to the MongoDB database!")
# db = app.mongodb_client.flask_db
# todos = db.todos

# @app.route('/', methods=('GET', 'POST'))
# def index():
#     if request.method=='POST':
#         content = request.form['content']
#         degree = request.form['degree']
#         todos.insert_one({'content': content, 'degree': degree})
#         return redirect(url_for('index'))

#     all_todos = todos.find()
#     return render_template('index.html', todos=all_todos)

@app.route('/i', methods=('GET', 'POST'))
def index2():
    return render_template('dashboard.html', days=["Monday", "Tues"])


@app.route('/c', methods=('GET', 'POST'))
def indexc():
    return render_template('dashboard.html', days=["Monday", "Tues"])


@app.route('/h', methods=('GET', 'POST'))
def index4():
    return render_template('dashboard2.html', days=["Monday", "Tues"])


@app.route('/o', methods=('GET', 'POST'))
def index3():
    return render_template('dashboardoriginal.html', days=["Monday", "Tues"])


# import paho.mqtt.client as mqtt


# MQTT client object
mqttc = None

# Topic to subscribe to.
# ***CHANGE THIS TO SOMETHING UNIQUE***
TOPIC = "iot-mrloh"


# Handles an MQTT client connect event
# This function is called once, just after the mqtt client is connected to the server.
def handle_mqtt_connack(client, userdata, flags, rc) -> None:
    print(f"MQTT broker said: {mqtt.connack_string(rc)}")
    if rc == 0:
        client.is_connected = True

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(f"{TOPIC}")
    print(f"Subscribed to: {TOPIC}")
    print(f"Publish something to {TOPIC} and the messages will appear here.")


# Handles an incoming message from the MQTT broker.
def handle_mqtt_message(client, userdata, msg) -> None:
    print(
        f"received msg | topic: {msg.topic} | payload: {msg.payload.decode('utf8')}")


# @app.route('/data2')
# def getDataUV():


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
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


@app.post('/<id>/delete/')
def delete(id):
    todos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))


def main() -> None:
    global mqttc

    # Create mqtt client
    mqttc = mqtt.Client()

    # Register callbacks
    mqttc.on_connect = handle_mqtt_connack
    mqttc.on_message = handle_mqtt_message

    # Set this flag to false first, handle_mqtt_connack will set it to true later
    mqttc.is_connected = False

    # Connect to broker
    mqttc.connect("broker.mqttdashboard.com")

    # start the mqtt client loop
    mqttc.loop_start()

    # approximate amount of time to wait for client to be connected
    time_to_wait_secs = 5

    # keep looping until either the client is connected, or waited for too long
    waited_for_too_long = False
    while not mqttc.is_connected and not waited_for_too_long:

        # sleep for 0.1s
        time.sleep(0.1)
        time_to_wait_secs -= 0.1

        # set this to true if waited for too long
        if time_to_wait_secs <= 0:
            waited_for_too_long = True

    # exit if client couldn't connect even after waiting for a long time
    if waited_for_too_long:
        logger.error(
            f"Can't connect to broker.mqttdashboard.com, waited for too long")
        return

    # Loopy loop
    # Keep looping, when messages come in they'll be handled by handle_mqtt_message()
    while True:
        time.sleep(10)

    # Stop the MQTT client
    mqttc.loop_stop()

# main()


if __name__ == '__main__':
    app.mongodb_client = MongoClient(config["ATLAS_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to the MongoDB database!")

    app.run(host='0.0.0.0', port=5012, debug=True)
    # main()
