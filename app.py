
from flask import Flask, request, jsonify, current_app, session
import pymysql
from flask_cors import *

app = Flask(__name__)
CORS(app, resources=r'*')
app.config['DBHOST'] = 'foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com'
app.config['DBUSER'] = 'admin'
app.config['DBPWD'] = '1q2w3e4r'
app.config['DBNAME'] = 'userdb'
app.config['DBPORT'] = 3306
app.config['SECRET_KEY'] = 'test123ASLDFJKLJK1JKL23JKLd123b'

response_template = {'code':200, 'msg':'',  'data':''}

@app.route('/user/login', methods=['POST'])
def login():
    if request.method == 'POST':
        db = pymysql.connect(
                host = current_app.config.get('DBHOST'),
                port = current_app.config.get('DBPORT') ,
                user = current_app.config.get('DBUSER'),
                password = current_app.config.get('DBPWD'),
                database = current_app.config.get('DBNAME')
                )
        cursor = db.cursor()
        data = request.get_json()
        username = data['username']
        password = data['password']
        sql = "select * from user where username='"+ username + "' and password='"+ password +"'"
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            if len(results)==1:
                session['username'] = username
                db.close()
                return jsonify({'code':200, 'msg':'user login successfully',  'data':{'username':username} })
            else:
                return jsonify({'code':404, 'msg':'username and password not matched, or username not exists!',  'data':''})
            db.commit()
        except Exception as e:
            print('exception - {}'.format(str(e)))
            db.rollback()
            return jsonify({'code':502, 'msg':'Exception occuried, please retry!',  'data':''})
      

@app.route('/user/register', methods=['POST'])
def register():
    if request.method == 'POST':
        db = pymysql.connect(
                host = current_app.config.get('DBHOST'),
                port = current_app.config.get('DBPORT') ,
                user = current_app.config.get('DBUSER'),
                password = current_app.config.get('DBPWD'),
                database = current_app.config.get('DBNAME')
            )
        data = request.get_json()

        username = data['username']
        password = data['password']
        password2 = data['password2']
      
        if password != password2:
            return jsonify({'code':502, 'msg':'Two password not matched, please check!',  'data':''})
        querysql = "select * from user where username='"+ username+"' and password='"+ password +"'"
        sql = "INSERT INTO user (username, password) VALUES ('"+ username +"', '"+ password +"')"
           
        try: 
            cursor = db.cursor()
            cursor.execute(querysql)
            results = cursor.fetchall()
            if len(results)==1:
                db.close()
                return jsonify({'code':500, 'msg':'user exists already, please check',  'data': '' })
            else:
                cursor.execute(sql)
                db.commit()
                session['username'] = username
                return jsonify({'code':200, 'msg':'user is created successfully',  'data': {'username':username} })
        except Exception as e:
            print('exception - {}'.format(str(e)))
            db.rollback()
            db.close()
            return jsonify({'code':502, 'msg':'Exception occuried, please retry!',  'data':''})
      
@app.route('/user/logout')
def logout():
    session.pop('username', None)
    return jsonify({'code':200, 'msg':'user logout successfully',  'data':'' })
@app.route('/health')
def health():
    return jsonify({'code':200, 'msg':'hi',  'data':'' })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
