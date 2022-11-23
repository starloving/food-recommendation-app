import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
import io


import torchvision
from torchvision import datasets, models, transforms

import numpy as np
import time
from flask import Flask, jsonify, request


device = torch.device('cpu') # device 객체

app = Flask(__name__)

class_names = ['갈비', '갈비탕', '감자탕', '고기구이', '국수', '김밥', '김치찌개',
    '깐풍기', '꿔바로우', '나베', '낙곱새', '냉면', '덮밥', '돈까스', '돼지국밥', '된장찌개', '떡국',
    '떡볶이', '라면', '마라샹궈', '마라탕', '매운탕', '버섯전골', '보쌈', '볶음밥', '부대찌개', '비빔밥',
    '샌드위치', '샐러드', '생선구이', '생선까스', '샤브샤브', '설렁탕', '소머리국밥', '순두부찌개', '스테이크',
    '육회', '족발', '짜장면', '짬뽕', '초밥', '치킨', '콩나물국밥', '탕수육', '토스트', '파스타', '폭립', '피자',
    '해물찜', '햄버거', '회덮밥']

model = torch.load("model_final.pt", map_location = device)
print(device)
transforms_test = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
print(device)
def get_prediction(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    image = transforms_test(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        _, preds = torch.max(outputs, 1)
\
    return class_names[preds[0]]

