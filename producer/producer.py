#!/usr/bin/env python

import sys
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Producer
import io
import mysql
import mysql.connector
from mysql.connector import errorcode
import json
from bson import json_util
import time
    
if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])

    # Create Producer instance
    producer = Producer(config)

    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered or permanently
    # failed delivery (after retries).
    def delivery_callback(err, msg):
        if err:
            print('ERROR: Message failed delivery: {}'.format(err))
        else:
            print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
                topic=msg.topic(), key=msg.key().decode("utf-8"), value=msg.value().decode("utf-8")))

    cnx = mysql.connector.connect(user='your_mysql_username_goes_here', password='your_mysql_password_goes_here', host='localhost', database='Dot')
    cursor = cnx.cursor()
    
    try:
        while True:
        
            time.sleep(5)
            
            print("Checking...")
            
            select = ("SELECT id FROM marked_for_deletion")
            cursor.execute(select)
            row_headers=[x[0] for x in cursor.description] 
            rv = cursor.fetchall()
            json_data=[]
            for result in rv:
                json_data.append(dict(zip(row_headers,result)))
            cnx.commit()
            
            for json_obj in json_data:
                topic = "DotToBeDeletedTopic"
                value={ 'id': json_obj["id"] , 'deleted': True }
                key={ 'id': json_obj["id"] }
                producer.produce(topic, json.dumps(value, default=json_util.default).encode('utf-8'), json.dumps(key, default=json_util.default).encode('utf-8'), callback=delivery_callback)
                producer.poll(10000)
                producer.flush()
                del_qry_data = ( json_obj["id"], )
                cursor.execute("DELETE FROM marked_for_deletion WHERE id = %s", del_qry_data)
                cnx.commit()
                
    except KeyboardInterrupt:
        pass
    finally:
        cursor.close()
        cnx.close()            