import pymysql
import pandas as pd
from pandas import DataFrame, Series
import numpy as np

#cosine 유사도 함수
def cosine_sim(a, b):
    if (np.linalg.norm(a) * (np.linalg.norm(b)))
    return np.dot(a, b) / (np.linalg.norm(a) * (np.linalg.norm(b)))

def Loadfooddataeset (input_food_list):
    '''
    
    '''
    #data base 접근
    conn = pymysql.connect(
        host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
        user = 'admin',
        password = '1q2w3e4r',
        db = 'food',
        charset = 'utf8'
    )
    cur =conn.cursor()

    Types = list()
    food_list = list()

    # input_food들의 type 추출  ex) 한식, 중식 ...
    for i_food in input_food_list :    
        query = "select type from food where f_name = (%s)"
        cur.execute(query,(i_food))
        rows = cur.fetchall()
        for row in rows :
            tmp = str(row).split("'")[1]
            Types.append(tmp)
    
    # 중복 type 제거
    Types = set(Types)

    # type이 같은 food_name, feature 추출 
    for Type in Types :
        query = "select * from ingredient left outer join food on ingredient.f_name = food.f_name where food.type = (%s)"
        cur.execute(query,(Type))
        rows = cur.fetchall()
        for row in rows :
            food_list.append(row[:-2])

    
    #index = 음식이름, dataframe = feature, 음식같의 vector
        
    df = DataFrame(np.array(food_list).transpose()[1:].transpose(), index = np.array(food_list).transpose()[0])

    df1 = df.drop(index = input_food_list)  # input 음식들을 추천에서 제외
    conn.close()

    return df1

def Loadfoodfeature(input_food_list) :
    conn = pymysql.connect(
        host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
        user = 'admin',
        password = '1q2w3e4r',
        db = 'food_info',
        charset = 'utf8'
    )
    cur = conn.cursor()
    #input_food_feature 초기화
    input_food_feature = np.zeros(14)
    for food in input_food_list :
        query = "select * from ingredient where f_name = (%s)"
        cur.execute(query,(food))
        rows = cur.fetchall()
        for row in rows :
            input_food_feature += np.array(row[1:])
    input_food_feature = input_food_feature / len(input_food_list)
    conn.close()

    return input_food_feature

# input = ['감자탕','마라탕','냉면'] 

def foodrm (input_list) :
    '''
        input : food name list
    '''

    if ( len(input_list) == 0 ) : 
        return rmlist , urllist

    df = Loadfooddataeset(input_list)
    food_feature = Loadfoodfeature(input_list)


    # { 음식이름 : 코사인 유사도 } 사전생성
    f_dict = dict()
    indexes = df.index
    for index in indexes :
        f_dict.update({index : cosine_sim(food_feature, np.array(df.loc[index], dtype = np.float64))})

    rank = sorted(f_dict.items(), key = (lambda x:x[1]), reverse =True)

    conn = pymysql.connect(
        host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
        user = 'admin',
        password = '1q2w3e4r',
        db = 'food',
        charset = 'utf8'
    )
    cur =conn.cursor()

    #코사인 유사도 value 기준으로  reverse sort


    #상위 3개 list 반환 
    rmlist = np.array(rank[:5]).transpose()[0].tolist()
    urllist = []
    
    
    for name in rmlist :
        sql = "select url from food where name =" + name
        cur.execute(sql)
        urllist.append(cur.fetchall()[0][0])    
    

    return rmlist, urllist