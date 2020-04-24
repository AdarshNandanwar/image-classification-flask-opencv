from flask import Flask, render_template, url_for, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import os


app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]


# DATABASE
# /// = relative path, //// = absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filestorage.db'
db = SQLAlchemy(app)

class FileContents(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200))
    data = db.Column(db.String(200))
    date_uploaded = db.Column(db.DateTime, default = datetime.utcnow)

    def __repr__(self):
        return '<Image %r>' % self.id

# Steps to create DB:
# open python interactive shell
# >>> from app import db
# >>> db.create_all()
# >>> exit()






# ROUTES
@app.route('/', methods = ['POST', 'GET'])
def index():
    if request.method == 'POST' and len(request.files['uploadPic'].filename) and allowed_image(request.files['uploadPic'].filename):
        file = request.files['uploadPic']
        new_pic = FileContents(name=file.filename)
        # file.save(os.path.join(target, str(new_pic.id)))
        try:
            db.session.add(new_pic)
            db.session.flush()
            filename = secure_filename(file.filename)
            target = os.path.join(APP_ROOT, 'static/images/')
            file.save(os.path.join(target, str(new_pic.id)))
            new_pic.data = findFaces(new_pic.id)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            print(e)
            return 'There was problem uploading your image'

    else:
        pics = FileContents.query.order_by(FileContents.date_uploaded).all()
        return render_template('index.html', pics = pics)

@app.route('/delete/<int:id>', methods = ['POST', 'GET'])
def delete(id):
    pic_to_delete = FileContents.query.get_or_404(id)

    try:
        db.session.delete(pic_to_delete)
        db.session.commit()
        target = os.path.join(APP_ROOT, 'static/images/')
        os.remove(os.path.join(target, str(pic_to_delete.id)))
        return redirect('/')
    except:
        return 'There was a problem deleting that pic'

@app.route('/update/<int:id>', methods = ['POST', 'GET'])
def update(id):
    pic = FileContents.query.get_or_404(id)
    if request.method == 'POST':
        file = request.files['uploadPic']
        pic.name = file.filename
        try:
            target = os.path.join(APP_ROOT, 'static/images/')
            os.remove(os.path.join(target, str(pic.id)))
            file.save(os.path.join(target, str(pic.id)))
            pic.data = findFaces(pic.id)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was a problem updating that pic'

    else:
        return render_template('update.html', pic = pic)


@app.route('/img/<int:img_id>')
def serve_img(img_id):
    pic = FileContents.query.get_or_404(img_id)
    return send_file(BytesIO(pic.name), attachment_filename=pic.name, mimetype='image/jpg')







def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False





# OpenCV
def findFaces(id):
    faceCascade = cv2.CascadeClassifier(os.path.join(APP_ROOT, 'static/classifiers/haarcascade_frontalface_default.xml'))
    target = os.path.join(APP_ROOT, 'static/images/')
    img = cv2.imread(target+str(id))
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(imgGray, 1.1, 4)
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    print(img)
    cv2.imwrite(target+str(id)+'__masked.jpg', img) 
    return "Faces found: "+str(len(faces))



if __name__ == "__main__":
    app.run(debug=True)