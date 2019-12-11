from flask import Flask, send_file, request
from flask_cors import CORS, cross_origin
app=Flask(__name__)
CORS(app, support_credentials=True)

@app.route('/')
def hello_world():
    return 'Hello, World!'

table = '''{
  "students": [
    {
        "ra": "170911",
        "signatures": [
          {
            "date": "01/01/2000",
            "raImage": "Auth1-cell-01-01.png",
            "signatureImage": "170911-01-01-2000-MC404-AB-SIGNATURE.jpg",
            "present": "true",
            "similar": "true",
            "checkoutValue": "PS"
          },
          {
            "date": "01/01/2000",
            "raImage": "170911-01-01-2000-MC404-AB-RA.jpg",
            "signatureImage": "170911-01-01-2000-MC404-AB-SIGNATURE.jpg",
            "present": "true",
            "similar": "true",
            "checkoutValue": "PS"
          }
        ]
    },
    {
        "ra" : "170911",
        "signatures": [
          {
            "date": "01/01/2000",
            "raImage": "170911-01-01-2000-MC404-AB-RA.jpg",
            "signatureImage": "170911-01-01-2000-MC404-AB-SIGNATURE.jpg",
            "present": "true",
            "similar": "true",
            "checkoutValue": "PS"
          },
          {
            "date": "01/01/2000",
            "raImage": "170911-01-01-2000-MC404-AB-RA.jpg",
            "signatureImage": "170911-01-01-2000-MC404-AB-SIGNATURE.jpg",
            "present": "true",
            "similar": "true",
            "checkoutValue": "PS"
          }
        ]
    }
  ]
}'''



@app.route('/painTable')
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def pain_table():
    return table

@app.route('/image')
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def get_image():
    filename = request.args.get('img')
    #filename = "ra170911-08_11_2019.png"
    return send_file("cells/" + filename, mimetype='image/png')