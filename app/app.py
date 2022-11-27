
from flask import Flask, request, jsonify, current_app, session
import pymysql
from flask_cors import *
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
import io

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

import torchvision
from torchvision import datasets, models, transforms

import numpy as np
import time
import collaborative_filtering as cf
import food_predict as fp
import contents_based_filtering as cbf

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
                port = current_app.config.get('DBPORT'),
                user = current_app.config.get('DBUSER'),
                password = current_app.config.get('DBPWD'),
                database = current_app.config.get('DBNAME')
                )
        fdb = pymysql.connect(
                host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
                user = 'admin',
                password = '1q2w3e4r',
                db = 'fooddb',
                charset = 'utf8'
                )
        data = request.get_json()
        print(data)
        username = data['username']
        password = data['password']
        password2 = data['password2']
        gender = data['gender']
        age = data['age']
        foodtype = data['foodtype']

        if password != password2:
            return jsonify({'code':502, 'msg':'Two password not matched, please check!',  'data':''})
        
        querysql = "select * from user where username='"+ username+"' and password='"+ password +"'"
        # sql = "INSERT INTO user (username, password, gender, age) VALUES ('"+ username +"', '"+ password +"', '"+ gender +"', '"+ age +"')"  
        findmax = 'select max(UserID) from user'
        try :    
            cursor = db.cursor()
            cur = fdb.cursor()
            cursor.execute(querysql)
            results = cursor.fetchall()
            if len(results)==1:
                db.close()
                fdb.close()
                return jsonify({'code':500, 'msg':'user exists already, please check',  'data': '' })
            else:
                cursor.execute(findmax)
                num = cursor.fetchall()[0][0] + 1
                sql = "INSERT INTO user (UserID ,username, password, gender, age) VALUES ('"+ str(num)+ "', '" + username +"', '"+ password +"', '"+ gender +"', '"+ age +"')"  
                cursor.execute(sql)
                db.commit()
                for Type in foodtype :
                    foodsql = " select FoodID from (food natural join feature) where type = " +"'" + Type + "'"
                    cur.execute(foodsql)
                    data = cur.fetchall()
                    for FoodId in data :
                        item_query = "insert into item (UserId, FoodId) values ('" +str(num)+"',' "+ str(FoodId[0]) + " ') " 
                        cursor.execute(item_query)
                    db.commit()
                db.close()
                fdb.close()    
                session['username'] = username
                return jsonify({'code':200, 'msg':'user is created successfully',  'data': {'username':username} })
        except Exception as e:
            print('exception - {}'.format(str(e)))
            db.rollback()
            db.close()
            fdb.close()
            return jsonify({'code':502, 'msg':'Exception occuried, please retry!',  'data':''})
      
@app.route('/user/logout')
def logout():
    session.pop('username', None)
    return jsonify({'code':200, 'msg':'user logout successfully',  'data':'' })
@app.route('/user/updateitem', methods = ['POST'])
def updateitem():
    if request.method == 'POST' :
        data = request.get_json()
        username = data['username']
        selectedfoodlist = data['selectedfoodlist']
        # db connect food, user
        db = pymysql.connect(
                host = current_app.config.get('DBHOST'),
                port = current_app.config.get('DBPORT'),
                user = current_app.config.get('DBUSER'),
                password = current_app.config.get('DBPWD'),
                database = current_app.config.get('DBNAME')
                )
        fdb = pymysql.connect(
                host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
                user = 'admin',
                password = '1q2w3e4r',
                db = 'fooddb',
                charset = 'utf8'
                )
        # find user id
        cursor = db.cursor()
        cur = fdb.cursor()

        query = "select UserID from user where username =" + "'" + username + "'"
        cursor.execute(query)
        userid = cursor.fetchall()[0][0]

        # find food id
        for food in selectedfoodlist :

            query = "select FoodID from food where name = " + "'" + food + "'"
            cur.execute(query)
            foodid = cur.fetchall()[0][0]

            
        # insert food id into user id
            insertqeury = "insert into item (UserID, FoodID ) values (" + str(userid) + "," + str(foodid) + ")"
            cursor.execute(insertqeury)
        
        db.commit()
        
        db.close()
        fdb.close()
        
        return jsonify({'code': 200, 'msg' : 'items are updated'})
@app.route('/health')
def health():
    return jsonify({'code':200, 'msg':'hi',  'data':'' })
@app.route('/predict', methods =['POST']) 
def predict():
    if request.method == 'POST':
        file = request.files['file']
        image_bytes = file.read()

        class_name = fp.get_prediction(image_bytes=image_bytes)
        print("결과:", {'class_name': class_name})
        return jsonify({'class_name': class_name})
@app.route('/cfalgorithm', methods=['POST'])
def cfalgorithm() :
    if request.method == 'POST' :
        data = request.get_json()
        username = data['username']
        rmlist, urllist, kcal, comment = cf.foodrm(username)

        return jsonify({'rmlist' : rmlist, 'urllist' : urllist, 'kcal' : kcal, 'comment': comment})
    else :
        return jsonify({'msg' : 'CFalgorithm Error'})

@app.route('/CBFalgorithm', methods=['POST'])
def CBFalgorithm() :
    if request.method == 'POST' :
        data = request.get_json()
        input_list = data['food_list']
        rmlist, urllist, kcal, comment = cbf.foodrm(input_list)
        return jsonify({'rmlist' : rmlist, 'urllist' : urllist, 'kcal' : kcal, 'comment': comment})
    else :
        return jsonify({'msg' : 'CBFalgorithm Error'})
@app.route('/satisfaction' , methods = ['POST'])
def satisfaction() :
    if request.method == 'POST' :
        data = request.get_json()
        satisfy = data['satisfy']
        ratings = data['ratings']
        msg = data['msg']

        # connect satisfaction db
        sdb = pymysql.connect(
            host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
            user = 'admin',
            password = '1q2w3e4r',
            db = 'satisfydb',
            charset = 'utf8'
            )
        scur = sdb.cursor()
        # insert data 
        query = "insert into satisfy (satisfy, rating, msg ) values ( "+ str(satisfy) + "," + str(ratings) + ", '" + msg + "')" 
        scur.execute(query)
        sdb.commit()
        sdb.close()
        
        # close db
        return jsonify({'code' : 200 , 'msg' : 'satisfaction updated'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
