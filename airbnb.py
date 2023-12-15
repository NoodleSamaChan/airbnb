from flask import Flask, request, jsonify
import base64
import psycopg2

app = Flask(__name__)

app.config['SERVER_NAME'] = '127.0.0.1:5000'

app.url_for('static', filename='index.html')

def cookie_creation(user_name, password):
    cookie = f'{user_name}:{password}'
    secret = 'airbnb'
    final_cookie = []
    for k in range(len(cookie)):
        final_cookie.append((ord(cookie[k]) ^ ord(secret[k%len(secret)])))
    
    base64_bytes = base64.b64encode(bytes(final_cookie))
    base64_message = base64_bytes.decode('utf-8')

    return base64_message

def cookie_decoding(cookie):

    base64_img_bytes = cookie.encode('utf-8')

    decoded_image_data = base64.decodebytes(base64_img_bytes)
    decoded = ''
    secret = 'airbnb'
    for k in range(len(decoded_image_data)):
        decoded = decoded + chr(decoded_image_data[k] ^ ord(secret[k%len(secret)]))
    final_decode = decoded.split(':')
    return final_decode

#connection to PGRSQL database
postgre_sql = psycopg2.connect("dbname=airbnb user=postgres password=postgres")
postgre_sql.set_session(autocommit=True)
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
def create_user():
    content = request.json
    try:
        cur.execute("""INSERT INTO users (account_name, account_password) VALUES (%s, %s)""", (content['fullName'], content['password']))
        cookie = cookie_creation(content['fullName'], content['password'])
        return jsonify({"status":"success", "cookie":cookie})
    except psycopg2.errors.UniqueViolation:
        print('User already exists')
        response = jsonify({"status":"user name already taken"})
        response.status = 408
        return response
    
#Login of users
@app.route("/user/login", methods=['POST'])
def user_login():
    content = request.json
    cur.execute("""SELECT account_name, account_password FROM users WHERE account_name = %s AND account_password = %s""", (content['fullName'], content['password']))
    result = cur.fetchall()
    if len(result) == 0:
        reponse = jsonify({"status":"account doesn't exist"})
        reponse.status = 404
        return reponse
    else:
        cookie = cookie_creation(content['fullName'], content['password'])
        return jsonify({"status":"success", "cookie":cookie})

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
        query_request = query_request + " AND title LIKE '{search}' LIMIT {limit} OFFSET {limit}".format(search=args['search'], limit=args["limit"])
    cur.execute(query_request)
    print(query_request)

    #changing the array result into an organised table
    result = cur.fetchall()
    result_table = []
    print(result)
    
    for i in result:
        print('lunaluna')
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

def validate_cookie(request):
    header = request.headers
    if header.get('Authorization') == None:
        reponse = jsonify({"status":"must be logged in"})
        reponse.status = 401
        return reponse
    else:
        result = header['Authorization'].split(' ')
        account_information = cookie_decoding(result[1])
        print(account_information)
        cur.execute("""SELECT account_name, account_password FROM users WHERE account_name = %s AND account_password = %s""", (account_information[0], account_information[1]))
        account_verification = cur.fetchall()
        if len(account_verification) == 0:
            reponse = jsonify({"status":"not authorized"})
            reponse.status = 401
            return reponse
        else:
            return None

@app.route("/lair", methods=['POST'])
def new_form():
    verification = validate_cookie(request)
    if verification == None:
        content = request.json
        print(content)
        cur.execute("""
        INSERT INTO announcements (title, image, description, lon, lat) 
        VALUES (%s, %s, %s, %s, %s)
        """, (content['title'], content['image'], content['description'], content['lon'], content['lat']))
        return jsonify({"status":"success"})
    else:
        return verification

@app.route("/lair/<id>", methods=['DELETE'])
def delete_form(id):  
    verification = validate_cookie(request)
    if verification == None:
        cur.execute("DELETE FROM announcements WHERE id = %s", (id))
        return jsonify({"status":"success"})
    else:
        return verification

@app.route("/debug", methods=['GET'])
def debug():
    cur.execute("SELECT * FROM announcements")
    return jsonify(cur.fetchall())

app.run()