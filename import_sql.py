# import thu vien
import os

from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import  Model

from PIL import Image
import pickle
import numpy as np
import mysql.connector
from PIL import Image
import requests
from io import BytesIO
# ----------------''-----------------
# connect to database
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root",
  database="clothing_store"
)


# Ham tao model
def get_extract_model():
    vgg16_model = VGG16(weights="imagenet")
    extract_model = Model(inputs=vgg16_model.inputs, outputs = vgg16_model.get_layer("fc1").output)
    return extract_model

# Ham tien xu ly, chuyen doi hinh anh thanh tensor
def image_preprocess(img):
    img = img.resize((224,224))
    img = img.convert("RGB")
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    return x

def extract_vector(model, image_path):
    print("Training file : ", image_path)
    response = requests.get(image_path)
    img = Image.open(BytesIO(response.content))
    # img = Image.open(image_path)
    img_tensor = image_preprocess(img)

    # Trich dac trung
    vector = model.predict(img_tensor)[0]
    # Chuan hoa vector = chia chia L2 norm (tu google search)
    vector = vector / np.linalg.norm(vector)
    return vector


def extract_vector_static(model, image_path):
    print("Xu ly : ", image_path)
    img = Image.open(image_path)
    img_tensor = image_preprocess(img)

    # Trich dac trung
    vector = model.predict(img_tensor)[0]
    # Chuan hoa vector = chia chia L2 norm (tu google search)
    vector = vector / np.linalg.norm(vector)
    return vector

def json_transform(cursor):
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()

    json_data = []

    for result in data:
        json_data.append(dict(zip(row_headers, result))) 
    
    return json_data