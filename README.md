# Image Classifier

Web aplication made using Flask and OpenCV. User may upload any image which is classified into predefined classes. These are then displayed in the main page with the appropriate tags.

## Deployed Server
https://flaskapp-imageclassifier.herokuapp.com/


## Requirements
To run the server, you will need Flask, Flask-SQLAlchemy and OpenCV.

## Installation

Clone this repository into your system

```bash
git clone https://github.com/AdarshNandanwar/image-classification-flask-opencv.git
```

## Usage

Create and activate a virtualenv and install required dependencies.

```bash
source venv/bin/activate
pip install -r requirements.txt
```
Create the database (SQLAlchemy). For that, run python interactive shell and write the following code.
```bash
python
```
```python
>>> from app import db
>>> db.create_all()
>>> exit()
```
Run the server.
```bash
python app.py
```
