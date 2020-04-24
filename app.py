from flask import Flask, render_template, url_for, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
from datetime import datetime


import cv2



app = Flask(__name__)





# DATABASE
# /// = relative path, //// = absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filestorage.db'
db = SQLAlchemy(app)

class FileContents(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200))
    data = db.Column(db.LargeBinary)
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
    if request.method == 'POST':
        file = request.files['uploadPic']
        new_pic = FileContents(name=file.filename, data=file.read())

        try:
            db.session.add(new_pic)
            db.session.commit()
            return redirect('/')
        except:
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
        return redirect('/')
    except:
        return 'There was a problem deleting that pic'

@app.route('/update/<int:id>', methods = ['POST', 'GET'])
def update(id):
    pic = FileContents.query.get_or_404(id)
    if request.method == 'POST':
        file = request.files['uploadPic']
        pic.name = file.filename
        pic.data = file.read()
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was a problem updating that pic'

    else:
        return render_template('update.html', pic = pic)


@app.route('/img/<int:img_id>')
def serve_img(img_id):
    pic = FileContents.query.get_or_404(img_id)
    return send_file(BytesIO(pic.data), attachment_filename=pic.name, mimetype='image/jpg')



if __name__ == "__main__":
    app.run(debug=True)