import logging
import json
import RPi.GPIO as GPIO
from time import sleep
from dragino import Dragino
from flask import Flask, request, jsonify
from waitress import serve
from paste.translogger import TransLogger

app = Flask(__name__)

logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

# create a Dragino object and join to TTN
D = Dragino("dragino.toml", logging_level=logging.INFO)
D.join()

logger.info("Waiting for JOIN ACCEPT")
while not D.registered():
    print(".",end="")
    sleep(2)
logger.info("TTN network joined")

@app.route("/api/v1/send", methods=['POST'])
def send():
    content = json.dumps(request.json)
    logger.info(content)
    D.send(content)
    while D.transmitting:
        sleep(0.1)
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    serve(TransLogger(app, setup_console_handler=False), host="0.0.0.0", port=8080)
