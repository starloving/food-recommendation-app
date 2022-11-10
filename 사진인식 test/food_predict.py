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

class_names = ['감자탕', '김치찌개', '냉면']
model = torch.load("model_3.pt", map_location = device)
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

    return class_names[preds[0]]
