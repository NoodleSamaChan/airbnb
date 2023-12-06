from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

app.config['SERVER_NAME'] = '127.0.0.1:5000'

app.url_for('static', filename='index.html')

#connection to PGRSQL database
postgre_sql = psycopg2.connect("dbname=airbnb user=postgres password=postgres")
#creation of cursor to execute SQL commands
cur = postgre_sql.cursor()

#creation of the users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    account_name text UNIQUE NOT NULL PRIMARY KEY,
    account_password text NOT NULL
);
""")

#creation of the announcements table
cur.execute("""
CREATE TABLE IF NOT EXISTS announcements (
    account_name text references users(account_name),
    id SERIAL UNIQUE PRIMARY KEY, 
    title text NOT NULL, 
    image text NOT NULL, 
    description text NOT NULL, 
    lon DOUBLE PRECISION NOT NULL, 
    lat DOUBLE PRECISION NOT NULL
);
""")

@app.route("/")
def root():
    return app.send_static_file('index.html')

#creation of user
@app.route("/user", methods=['POST'])
def user():
    content = request.json
    cur.execute("""CREATE USER %s WITH PASSWORD '%s' AND INSERT INTO users (account_name, account_password) VALUES (%s, %s) """, (content['name'], content['password'], content['name'], content['password']))
    return jsonify({"status":"success"})

@app.route("/lair", methods=['GET'])
def look_for_lair():
    args = request.args
    print(args)
    # tl means top left
    # br means bottom right
    # Here's the shape fo the map:
    #    longitude
    # -180 <---> 180   90 
    # tl - - - -       ^
    #  - - - - -       | latitude
    #  - - - - br      v
    #                 -90
    query_request = "SELECT id, title, image, lon, lat FROM announcements WHERE lat > {br_lat} AND lat < {tl_lat} AND lon > {tl_lng} AND lon < {br_lng}"\
        .format(br_lat=args["br_lat"], br_lng=args["br_lng"], tl_lat=args["tl_lat"], tl_lng=args["tl_lng"]
    )
    print(query_request)
    if args.get('search') is not None:
        query_request = query_request + " AND title LIKE '{search}'".format(search=args['search'])
    cur.execute(query_request)

    #changing the array result into an organised table
    result = cur.fetchall()
    result_table = []
    print(result)
    
    for i in result:
        values = {}
        values['id'] = i[0]
        values['title'] = i[1]
        values['image'] = i[2]
        values['lon'] = i[3]
        values['lat'] = i[4]
        result_table.append(values)
    print(result_table)

    return jsonify(result_table)

@app.route("/lair/<id>", methods=['GET'])
def one_lair(id):
    cur.execute("SELECT * from announcements WHERE id = %s", (id))
    
    #changing the array result into an organised table
    result = cur.fetchall()
    result_table_id = []
    print(result)
    
    for i in result:
        values = {}
        values['id'] = i[0]
        values['title'] = i[1]
        values['image'] = i[2]
        values['lon'] = i[3]
        values['lat'] = i[4]
        result_table_id.append(values)
    print(result_table_id)

    return jsonify(result_table_id)

@app.route("/lair", methods=['POST'])
def new_form():   
    content = request.json
    print(content)
    cur.execute("""
    INSERT INTO announcements (title, image, description, lon, lat) 
    VALUES (%s, %s, %s, %s, %s)
    """, (content['title'], content['image'], content['description'], content['lon'], content['lat']))
    return jsonify({"status":"success"})

@app.route("/lair/<id>", methods=['DELETE'])
def delete_form(id):  
    cur.execute("DELETE FROM announcements WHERE id = %s", (id))
    return jsonify({"status":"success"}) 

@app.route("/debug", methods=['GET'])
def debug():
    cur.execute("SELECT * FROM announcements")
    return jsonify(cur.fetchall())

app.run()