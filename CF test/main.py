import math
import random
import pandas as pd
from collections import defaultdict
from operator import itemgetter
import pymysql
import numpy as np

def LoadMovieLensData(train_rate):
    """
    데이터 읽기 및 User-Item 테이블 만들기
    """
    conn = pymysql.connect(
    host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
    user = 'admin',
    password = '1q2w3e4r',
    db = 'userdb',
    charset = 'utf8'
    )
    cur = conn.cursor()
    sql = "select * from item order by UserID"
    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    conn.close()

    ratings = pd.DataFrame(data = result, columns= ['UserID','FoodID'])
    ratings = ratings[['UserID', 'FoodID']]
    train = []
    test = []
    random.seed(3)
    for idx, row in ratings.iterrows():
        try:
            user = int(row['UserID'])
            item = int(row['FoodID'])
        except ValueError as e:
            pass
        else:
            if random.random() < train_rate:
                train.append([user, item])
            else:
                test.append([user, item])
    return PreProcessData(train), PreProcessData(test)

def PreProcessData(originData):
    """
    User-Item 테이블을 작성하려면 다음과 같이 하십시오.：
        {"User1": {FoodID1, FoodID2, FoodID3,...}
         "User2": {FoodID12, FoodID5, FoodID8,...}
         ...
        }
    """
    trainData = dict()
    for user, item in originData:
        trainData.setdefault(user, set())
        trainData[user].add(item)
    return trainData

class UserCF(object):
    """ User based Collaborative Filtering Algorithm Implementation"""
    def __init__(self, trainData, similarity="cosine"):
        self._trainData = trainData
        self._similarity = similarity
        self._userSimMatrix = dict() # 사용자 유사도 행렬

    def similarity(self):
        # User-Item 역렬 테이블 만들기
        item_user = dict()
        for user, items in self._trainData.items():
            for item in items:
                item_user.setdefault(item, set())
                item_user[item].add(user)

        # 사용자 물품 교집 매트릭스 W를 구축하는데 그 중에서 C[u][v]는 사용자 u와 사용자 v 사이에 공통적으로 좋아하는 물품 수를 나타낸다
        for item, users in item_user.items():
            for u in users:
                for v in users:
                    if u == v:
                        continue
                    self._userSimMatrix.setdefault(u, defaultdict(int))
                    if self._similarity == "cosine":
                        self._userSimMatrix[u][v] += 1 #사용자 u와 사용자 v가 공동으로 좋아하는 물품 수량을 하나 더합니다
                    elif self._similarity == "iif":
                        self._userSimMatrix[u][v] += 1. / math.log(1 + len(users))

        # 사용자 유사도 매트릭스 만들기
        for u, related_user in self._userSimMatrix.items():
            # 싱크로율 공식은 |N[u]∩N[v]|/sqrt(N[u]||N[v])
            for v, cuv in related_user.items():
                nu = len(self._trainData[u])
                nv = len(self._trainData[v])
                self._userSimMatrix[u][v] = cuv / math.sqrt(nu * nv)

    def recommend(self, user, N, K):
        """
        사용자 u의 아이템 i에 대한 관심도:
            p(u,i) = ∑WuvRvi
            그 중에서 Wuv는 u와 v 간의 유사도를 대표하고 Rvi는 사용자 v가 물품 i에 대한 관심 정도를 대표한다. 단일 행위의 은밀한 피드백 데이터를 사용하기 때문에 Rvi=1이다.
            그래서 이 표현식의 의미는 사용자 u가 물품 i에 대한 관심 정도를 계산하려면 사용자 u와 가장 비슷한 K개 사용자를 찾아야 한다는 것이다. 이 k개 사용자가 좋아하는 물품과 사용자 u
            피드백이 없는 물품은 모두 사용자 u와 사용자 v 간의 유사도를 누적한다.
        :param user: 추천된 사용자user
        :param N: 추천 상품 개수
        :param K: 가장 유사한 사용자 수 찾기
        :return: 추천 아이템에 대한 유저의 관심 정도에 따라 정렬된 N개 상품
        """
        recommends = dict()
        # 사용자 피드백이 있는 item 그룹을 가져옵니다.
        related_items = self._trainData[user]
        # 다른 사용자와 사용자를 유사도 역순으로 정렬한 후 이전 K개 가져오기
        for v, sim in sorted(self._userSimMatrix[user].items(), key=itemgetter(1), reverse=True)[:K]:
            # 비슷한 사용자의 사랑 리스트에서 가능한 아이템을 찾아 추천합니다.
            for item in self._trainData[v]:
                if item in related_items:
                    continue
                recommends.setdefault(item, 0.)
                recommends[item] += sim
        # 추천된 아이템의 유사도에 따라 역순으로 배열한 후 이전 N개 아이템을 사용자에게 추천
        return dict(sorted(recommends.items(), key=itemgetter(1), reverse=True)[:N])

    def train(self):
        self.similarity()

def write_user_data(UserID,FoodID):
    """
    사용자 파일에 새 데이터 쓰기
    """
    
    conn = pymysql.connect(
    host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
    user = 'admin',
    password = '1q2w3e4r',
    db = 'userdb',
    charset = 'utf8'
    )
    cur = conn.cursor()
    for ID in FoodID :

        sql = "insert into item (UserId, FoodId) values ('" +str(UserID)+"',' "+ str(ID) + " ') " 
        cur.execute(sql)
    
    conn.commit()    
    conn.close()

    return "success"


if __name__ == "__main__":
    '''
        사용자 데이터 쓰기，
        예제： 
            UserID input：12
            FoodID output：1567,2564,6358,1896,2689,2515,6984,6581,11035
        '''
    UserID = input("please input UserID:")

    FoodID = list(map(int, input("please input FoodID:").split(",")))

#   write_user_data(UserID,FoodID)

    train, test = LoadMovieLensData(0.8)
    UserCF = UserCF(train)
    UserCF.train()
    conn = pymysql.connect(
        host='foodrm.cgnnqocprf5c.us-east-1.rds.amazonaws.com',
        user = 'admin',
        password = '1q2w3e4r',
        db = 'fooddb',
        charset = 'utf8'
        )
    cur = conn.cursor()
    # 사용자에게 각각 5개의 음식 추천
    rmlist = []
    for i in UserCF.recommend(int(UserID), 5, 8).keys():
        
        sql = "select name from food where FoodID =" + str(i)        
        cur.execute(sql)
        rmlist.append(cur.fetchall()[0][0])
    conn.close()
        
        
    print(rmlist)    
