from flask import Flask, request, Response
import mysql.connector
import json

app = Flask(__name__,
            static_url_path='', 
            static_folder='web/static',
            template_folder='web/templates')

@app.route('/dot')
def dot():
    try:
        cnx = mysql.connector.connect(user='your_mysql_user_goes_here', password='your_mysql_password_goes_here', host='mysql-db-1', database='Dot')
        cur = cnx.cursor()
        if(request.args.get('type') == 'full'): 
           cur.execute('SELECT id, label, x, y, radius, color, deleted, timestamp FROM Dot')
        else:
           cur.execute('SELECT id, label, x, y, radius, color, deleted, timestamp FROM Dot WHERE timestamp > (UNIX_TIMESTAMP()-10)*1000')
        row_headers=[x[0] for x in cur.description]  
        rv = cur.fetchall() 
        json_data=[]
        for result in rv:
             json_data.append(dict(zip(row_headers,result)))
        return Response(json.dumps(json_data), mimetype="application/json")
    finally:
        cur.close()
        cnx.close()

@app.route('/dot/<id>', methods=['DELETE'])
def delDot(id):
    cnx = mysql.connector.connect(user='your_mysql_user_goes_here', password='your_mysql_password_goes_here', host='mysql-db-1', database='Dot')
    cur = cnx.cursor()
    qry_data = ( id, )
    cur.execute("INSERT INTO marked_for_deletion(id) VALUES ( %s )", qry_data)
    cnx.commit()
    cur.close()
    cnx.close()
    return Response("", status=204)
