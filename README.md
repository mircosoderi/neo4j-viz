# neo4j-viz
Suppose you have `Dot` resources stored in your neo4j semantic database, each having its label, position, radius, and color. How do you display those dots on a Web page and keep them updated at real-time? How do you make them clickable, and soft delete them from the database when clicked? This repository provides answers for these questions.

# Overview

Events are published on a Kafka topic in Confluent every time that a change is made on `Dot` resources in Neo4j. The Confluent connector for Neo4j is used for this purpose.

The Python consumer client for Confluent Kafka subscribes to that topic and updates a MySql table. The MySql table is designed bearing in mind the intended usage of data, not the original structure of data in the semantic database.

A Python Flask application provides APIs to retrieve data from the database. Such APIs are invoked by a Javascript worker that pushes messages to a Web frontend that consists in an SVG embedded in an HTML page. The SVG is updated as messages flow from the worker. Both the backend and the frontend are part of the same application to avoid CORS issues.

In the opposite direction, the Web frontend posts messages to the worker when a dot is clicked. The worker makes an API request to the Flask application of which it is itself part. The API populates a MySQL table of dots marked for deletion. 

A Python producer client for Confluent Kafka reads from that MySQL table and publishes events to a configured topic every time that a new row is added. 

Every time that an event is published to the topic, a Cypher query is run on the Neo4j database to set the deleted property to true on the targeted `Dot` instance. The Confluent connector for Neo4j is used for this purpose. 

# Neo4j

For the purposes of this proof-of-concept, we will use a containerised Neo4j database. Cloud-based options are also available; please see the Neo4j website for details.

Please issue the following commands:

1. docker pull neo4j
2. docker volume create neo4j
3. docker run --publish=7474:7474 --publish=7687:7687 --volume=neo4j:/data --name=neo4j neo4j
4. Connect to localhost:7474, login with neo4j/neo4j and set your new password

# Confluent

For the purposes of this proof-of-concept, we will use a containerised Confluent platform. Cloud-based options are also available; please see the Confluent website for details.

Please see the [Docker Quickstart page](https://docs.confluent.io/platform/current/platform-quickstart.html#ce-docker-quickstart) on the Confluent Website for installation details.

Then, please get a shell of the `connect` container, and issue `confluent-hub install neo4j/kafka-connect-neo4j:5.0.3` to install the Neo4j connector.

# Docker User-defined Bridge Network

Please create a user-defined bridge network on Docker.

Please connect the `neo4j` and the `connect` containers to such network. 

Further containers will be added later. 

# Source Connector from Neo4j to Confluent

Please create a connector to publish events from Neo4j to a Confluent Kafka topic. 

Please make a POST request to `http://localhost:8083/connectors` to accomplish that. 

Please use the following as request body:

	{
	  "name": "DotConn",
	  "config": {
		"topic": "DotTopic",
		"connector.class": "streams.kafka.connect.source.Neo4jSourceConnector",
		"key.converter": "io.confluent.connect.avro.AvroConverter",
		"key.converter.schema.registry.url": "http://schema-registry:8081",
		"value.converter": "io.confluent.connect.avro.AvroConverter",
		"value.converter.schema.registry.url": "http://schema-registry:8081",
		"neo4j.server.uri": "bolt://neo4j:7687",
		"neo4j.authentication.basic.username": "neo4j",
		"neo4j.authentication.basic.password": "your_neo4j_password_goes_here",
		"neo4j.streaming.poll.interval.msecs": 5000,
		"neo4j.streaming.from": "LAST_COMMITTED",
		"neo4j.enforce.schema": true,
		"neo4j.source.query": "MATCH (d:Dot) WHERE d.timestamp > $lastCheck RETURN ID(d) as id, d.label as label, d.x as x, d.y as y, d.radius as radius, d.color as color, d.deleted as deleted, d.timestamp as timestamp",
		"transforms": "ValueToKey",
		"transforms.ValueToKey.type": "org.apache.kafka.connect.transforms.ValueToKey",
		"transforms.ValueToKey.fields": "id"
	  }
	}

# Test the connection

Please issue Cypher queries like the following and verify that corresponding events are published to the `DotTopic` topic on Confluent Kafka.

	CREATE (d:Dot {label: 'Bravo', x: 30, y: 30, radius: 10, color: 'blue', deleted: false, timestamp: timestamp()})

	MATCH(d:Dot) WHERE d.label = 'Bravo' set d.color = 'red', d.timestamp = timestamp()

Please remember to always generate or update the timestamp. The connector relies on that to determine when an event must be published. 

# MySql

For the purposes of this proof-of-concept, we will use a containerised MySql database.

Please refer to the `mysql` folder in this repository for running a properly initialised MySql container using Docker Compose.

Please connect the MySql container to the Docker User-defined Bridge Network created above.

# Kafka Consumer

Connecting the official Python client for Confluent to the Confluent platform when both the client and the platform are containerised [poses challenges](https://www.confluent.io/blog/kafka-client-cannot-connect-to-broker-on-aws-on-docker-etc/).

To make things work please either go through the blog post linked above, or run your consumer and producer applications on the Docker Host, not containerised.

Please refer to the `consumer` folder in this repository for the requirements and implementation of the Kafka consumer. 

See also:
1. https://developer.confluent.io/get-started/python/
2. https://dev.mysql.com/doc/connector-python/

# Test the consumer

Please create or update some `Dot` resources in the semantic database and verify that they correctly appear in the `Dot` table of the MySql database.

# Sink Connector from Confluent to Neo4j

Please create a connector to publish events from a Confluent Kafka topic to Neo4j.

Please make a POST request to `http://localhost:8083/connectors` to accomplish that. 

Please use the following as request body:

	{
	  "name": "DotProd",
	  "config": {
		"topics": "DotToBeDeletedTopic",
		"connector.class": "streams.kafka.connect.sink.Neo4jSinkConnector",
		"key.converter": "org.apache.kafka.connect.json.JsonConverter",
		"key.converter.schemas.enable": false,
		"value.converter": "org.apache.kafka.connect.json.JsonConverter",
		"value.converter.schemas.enable": false,
		"errors.retry.timeout": "-1",
		"errors.retry.delay.max.ms": "1000",
		"errors.tolerance": "all",
		"errors.log.enable": true,
		"errors.log.include.messages": true,
		"neo4j.server.uri": "bolt://neo4j:7687",
		"neo4j.authentication.basic.username": "neo4j",
		"neo4j.authentication.basic.password": "your_neo4j_password_goes_here",
		"neo4j.topic.cypher.DotToBeDeletedTopic": "MATCH (d:Dot) WHERE ID(d) = event.id SET d.deleted = event.deleted, d.timestamp = timestamp()"
	  }
	}

# Kafka Producer

Connecting the official Python client for Confluent to the Confluent platform when both the client and the platform are containerised [poses challenges](https://www.confluent.io/blog/kafka-client-cannot-connect-to-broker-on-aws-on-docker-etc/).

To make things work please either go through the blog post linked above, or run your consumer and producer applications on the Docker Host, not containerised.

Please refer to the `producer` folder in this repository for the requirements and implementation of the Kafka producer. 

# Test the producer

Please manually insert IDs of `Dot` instances in the `marked_for_deletion` MySql table, and verify that in the Neo4j database the `Dot` resource that bears that ID comes to have the `deleted` property set to true.

# Web Application

The Web application is a Python Flash application.

For the purposes of this proof-of-concept, we will run it containerised.

Please issue the following to run the container:

1. docker volume create web-app
2. docker run -it --volume=web-app:/usr/src/app --publish=5000:5000 --name=web-app python:3

Please connect the newly created container to the Docker User-defined Bridge Network created above.

Please refer to the `webapp` folder in this repository to know about the requirements, and the folder structure and artifacts that you have to create in the `/usr/src/app` in the newly created container. 

Please run `flask --app pywebapp run --host=0.0.0.0 -p 5000` from the `/usr/src/app` folder in the newly created container to start the Web application. 

Please connect to `http://localhost:5000` to see the application in action.

# Test the Web application

Create and update `Dot` resources in the Neo4j database, and after a few seconds you should be able to see the changes reflected on the Web.

Click dots in the Web application, and after a few seconds you should see the corresponding Neo4j resource updated, and the clicked dot disappear from the Web.