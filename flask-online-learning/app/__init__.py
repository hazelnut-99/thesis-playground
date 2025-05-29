from flask import Flask
from app.routes import create_model, fit, predict

def create_app():
    app = Flask(__name__)
    
    app.add_url_rule('/create_model/<model_name>', 'create_model', create_model, methods=['POST'])
    app.add_url_rule('/fit/<model_name>', 'fit', fit, methods=['POST'])
    app.add_url_rule('/predict/<model_name>', 'predict', predict, methods=['POST'])
    
    return app

app = create_app()