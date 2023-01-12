from flask import Flask
from threading import Thread
import os

app = Flask('')

host = os.environ['host']
port = int(os.environ['port'])

@app.route('/')
def home():
  return "Hello, I'm alive"

def run():
  app.run(host=host, port=port)

def keep_alive():
  t = Thread(target=run)
  t.start()