from flask import Flask, render_template, url_for, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import os
import enum

app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]


# DATABASE
# /// = relative path, //// = absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filestorage.db'
db = SQLAlchemy(app)

class FileContents(db.Model):
    __tablename__ = 'filecontent'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200))
    data = db.Column(db.String(200))
    date_uploaded = db.Column(db.DateTime, default = datetime.utcnow)
    tags = db.relationship('Tags', backref='filecontent', cascade = 'all, delete-orphan', lazy = 'dynamic')

    def __repr__(self):
        return '<Image %r>' % self.id

class Tags(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    image_file = db.Column(db.Integer, db.ForeignKey('filecontent.id'), nullable=False)
    tag = db.Column(db.String(20), nullable=False)

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
        try:
            db.session.add(new_pic)
            db.session.flush()
            filename = secure_filename(file.filename)
            target = os.path.join(APP_ROOT, 'static/images/')
            file.save(os.path.join(target+'uploads/', str(new_pic.id)))
            new_pic.data, is_pedestrian, is_face, is_car = classifyImage(new_pic.id)
            if is_pedestrian:
                db.session.add(Tags(image_file=new_pic.id, tag='Pedestrian'))
            if is_face:
                db.session.add(Tags(image_file=new_pic.id, tag='Face'))
            if is_car:
                db.session.add(Tags(image_file=new_pic.id, tag='Car'))
            db.session.commit()
            return redirect('/')
        except Exception as e:
            print(e)
            return 'There was problem uploading your image'

    else:
        data = []
        pics = FileContents.query.order_by(FileContents.date_uploaded).all()
        for pic in pics:
            tags = Tags.query.filter_by(image_file = pic.id)
            entry = {}
            entry['pic'] = pic
            entry['tags'] = tags
            data.append(entry)

        return render_template('index.html', data = data)

@app.route('/delete/<int:id>', methods = ['POST', 'GET'])
def delete(id):
    pic_to_delete = FileContents.query.get_or_404(id)

    try:
        Tags.query.filter_by(image_file = pic_to_delete.id).delete()
        db.session.delete(pic_to_delete)
        db.session.commit()
        target = os.path.join(APP_ROOT, 'static/images/')
        os.remove(os.path.join(target+'uploads/', str(pic_to_delete.id)))
        os.remove(os.path.join(target+'masked/', str(pic_to_delete.id)+'.jpg'))
        return redirect('/')
    except Exception as e:
        print(e)
        return 'There was a problem deleting that pic'

@app.route('/update/<int:id>', methods = ['POST', 'GET'])
def update(id):
    pic = FileContents.query.get_or_404(id)
    if request.method == 'POST':
        file = request.files['uploadPic']
        pic.name = file.filename
        try:
            target = os.path.join(APP_ROOT, 'static/images/')
            os.remove(os.path.join(target+'uploads/', str(pic.id)))
            os.remove(os.path.join(target+'masked/', str(pic.id)+'.jpg'))
            file.save(os.path.join(target+'uploads/', str(pic.id)))
            Tags.query.filter_by(image_file = pic.id).delete()
            pic.data, is_pedestrian, is_face, is_car = classifyImage(pic.id)
            if is_pedestrian:
                db.session.add(Tags(image_file=pic.id, tag='Pedestrian'))
            if is_face:
                db.session.add(Tags(image_file=pic.id, tag='Face'))
            if is_car:
                db.session.add(Tags(image_file=pic.id, tag='Car'))
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
def classifyImage(id):

    target = os.path.join(APP_ROOT, 'static/images/')
    img = cv2.imread(target+'uploads/'+str(id))
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # FULL BODY PEDESTRIANS
    bodyCascade = cv2.CascadeClassifier(os.path.join(APP_ROOT, 'static/cascade/haarcascade_fullbody.xml'))
    bodies = bodyCascade.detectMultiScale(imgGray, 1.1, 4)
    for (x, y, w, h) in bodies:
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 3)
    # FACES
    faceCascade = cv2.CascadeClassifier(os.path.join(APP_ROOT, 'static/cascade/haarcascade_frontalface_default.xml'))
    faces = faceCascade.detectMultiScale(imgGray, 1.1, 4)
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    # CARS
    carCascade = cv2.CascadeClassifier(os.path.join(APP_ROOT, 'static/cascade/haarcascade_car.xml'))
    cars = carCascade.detectMultiScale(imgGray, 1.1, 4)
    for (x, y, w, h) in cars:
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        
    cv2.imwrite(target+'masked/'+str(id)+'.jpg', img) 
    # return format: data, is_pedestrian, is_face, is_car
    return "Pedestrians found: "+str(len(bodies))+", Faces found: "+str(len(faces))+", Cars found: "+str(len(cars)), len(bodies)!=0, len(faces)!=0, len(cars)!=0 



if __name__ == "__main__":
    app.run(debug=True)