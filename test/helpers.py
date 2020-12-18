import json
import psycopg2
import os
import sys


def get_connection():
    try:
        connection = psycopg2.connect(user=os.environ["DB_USER"],
                                      password=os.environ["DB_PASS"],
                                      host=os.environ["DB_HOST"],
                                      port=os.environ["DB_PORT"],
                                      database=os.environ["DB_NAME"])
        return connection
    except Exception as e:
        sys.exit(e)


def load_sample_json(file):
    with open('test/sample_json/'+file) as sample_json:
        return json.load(sample_json)
