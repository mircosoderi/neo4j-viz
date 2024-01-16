#!/usr/bin/env python

import sys
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Consumer, OFFSET_BEGINNING
import io
import avro
from avro.io import DatumReader, BinaryDecoder
import mysql
import mysql.connector
from mysql.connector import errorcode

schema_key = avro.schema.parse(open("./schema-DotTopic-key-v1.avsc","r").read())
reader_key = DatumReader(schema_key)
schema_value = avro.schema.parse(open("./schema-DotTopic-value-v1.avsc","r").read())
reader_value = DatumReader(schema_value)

def decode_key(msg_value):
    message_bytes = io.BytesIO(msg_value)
    message_bytes.seek(5)
    decoder = BinaryDecoder(message_bytes)
    event_dict = reader_key.read(decoder)
    return event_dict
    
def decode_value(msg_value):
    message_bytes = io.BytesIO(msg_value)
    message_bytes.seek(5)
    decoder = BinaryDecoder(message_bytes)
    event_dict = reader_value.read(decoder)
    return event_dict

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])
    config.update(config_parser['consumer'])

    # Create Consumer instance
    consumer = Consumer(config)
    
    # Create DB connection
    cnx = mysql.connector.connect(user='your_mysql_user_goes_here', password='your_mysql_password_goes_here', host='localhost', database='Dot')
    cursor = cnx.cursor()

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            consumer.assign(partitions)

    # Subscribe to topic
    topic = "DotTopic"
    consumer.subscribe([topic], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                print("Consumed event from topic {topic}: key = {key} value = {value}".format(
                    topic=msg.topic(), key=decode_key(msg.key()), value=decode_value(msg.value())))                    
                add_dot = ("INSERT INTO Dot(id, label, x, y, radius, color, deleted, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE label = %s, x = %s, y = %s, radius = %s, color = %s, deleted = %s, timestamp = %s")
                dict_dot = decode_value(msg.value())                
                data_dot = ( dict_dot["id"], dict_dot["label"], dict_dot["x"], dict_dot["y"], dict_dot["radius"], dict_dot["color"], dict_dot["deleted"], dict_dot["timestamp"], dict_dot["label"], dict_dot["x"], dict_dot["y"], dict_dot["radius"], dict_dot["color"], dict_dot["deleted"], dict_dot["timestamp"])
                cursor.execute(add_dot, data_dot)
                cnx.commit()               
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        cursor.close()
        cnx.close()