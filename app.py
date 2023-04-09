from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import mysql.connector
from import_sql import *
from urllib.parse import quote
from werkzeug.utils import secure_filename

import openai   
import os
api_Key = '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'
os.environ['OPENAI_Key'] = api_Key
openai.api_key = os.environ['OPENAI_Key']

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# Khai bao noi luu anh sau khu user upload anh tim kiem
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root",
  database="clothing_store"
)

# check exist model: .pkl
if (os.path.isfile('products.pkl') == False or os.path.isfile('vectors.pkl') == False):
    print("model doesn't exist in this project!")
    # Khoi tao model
    model = get_extract_model()

    vectors = []
    products = []

    # define a cursor
    mycursor = mydb.cursor()

    # load data from database
    # mycursor.execute("SELECT ip.product_id, ip.image FROM clothing_store.images_product ip;")
    mycursor.execute("SELECT p.id, p.image FROM clothing_store.products p;")

    # add to array
    arr_img = []

    for x in mycursor:
        arr_img.append(x)

    # ----------------''-----------------
    # modeling data from database
    for url in arr_img:
        # trich dac trung cua tung anh
        image_vector = extract_vector(model, url[1])
        # product id tuong ung
        products.append(url[0])
        # add vao list
        vectors.append(image_vector)

    # save vao file, dump file và chuyển sang search_image
    vector_file = "vectors.pkl"
    product_file = "products.pkl"

    pickle.dump(vectors, open(vector_file, "wb"))
    pickle.dump(products, open(product_file, "wb"))

# Create api

# @cross_origin(origin='*',headers=['Content-Type','Authorization'])
@app.route('/search-by-image', methods=['POST'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def recommend():
    # Dinh nghia anh can tim kiem
    if 'files[]' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
 
    files = request.files.getlist('files[]')
     
    # search_image_path = "";
    errors = {}
    success = False
    for file in files:      
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            search_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(search_image_path)
            success = True
        else:
            errors[file.filename] = 'File type is not allowed'
 
    if success and errors:
        errors['message'] = 'File(s) successfully uploaded'
        resp = jsonify(errors)
        resp.status_code = 500
        return resp
    if success:
        # Khoi tao model
        model = get_extract_model()

        # Trich dac trung anh search
        search_vector = extract_vector_static(model, search_image_path)

        # Load 4700 vector tu vectors.pkl ra bien
        vectors = pickle.load(open("vectors.pkl","rb"))
        products = pickle.load(open("products.pkl","rb"))

        # Tinh khoang cach tu search_vector den tat ca cac vector
        distance = np.linalg.norm(vectors - search_vector, axis=1)

        # Sap xep va lay ra K vector co khoang cach ngan nhat
        K = 4
        # -> ra 4 san pham gan giong nhat
        ids = np.argsort(distance)[:K]

        # Tao oputput
        nearest_image = [(products[id], distance[id]) for id in ids]
        # Chua id cua product result
        img_result = []

        for id in range(K):
            print("img name : ", nearest_image[id][0])
            img_result.append(nearest_image[id][0])
        print("img result : ", img_result)

        # Chua san pham
        product_result = []
        # load data from database
        for id_product in img_result:
            mycursor = mydb.cursor()
            mycursor.execute("select p.id, p.name, p.avg_rating, p.image, t.price, c.countComment " +
                             "from products p, types t, (select count(*) as countComment " +
                             "from comments c, products p " +
                             "where c.product_id = p.id and p.id = " + str(id_product) + ") c " + 
                             "where p.id = t.product_id and p.id = " + str(id_product) +
                             " group by p.id")
            product_result += json_transform(mycursor)
            print(product_result)

            mycursor.close()
        
        return jsonify({'list': product_result})
        # resp = jsonify({'message' : 'Files successfully uploaded'})
        # resp.status_code = 201
        # return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp

# @cross_origin(origin='*',headers=['Content-Type','Authorization'])
@app.route('/auto-reply', methods=['POST'])
def autoBotReply():
    prompt = request.form.get("question")
    if prompt == "":
        print("Stop here!")

    resp = openai.Completion.create(
        model='text-davinci-003',
        prompt = prompt,
        max_tokens=1000
    )
        
    return(resp['choices'][0]['text'])

app.run(host='localhost', port=8081)