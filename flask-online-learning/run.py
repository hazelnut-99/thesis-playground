from flask import Flask
from app.routes import bp

app = Flask(__name__)

# Register the Blueprint
app.register_blueprint(bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)