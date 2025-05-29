from .sklearn_model import SGDModel


models = {}

def create_model(model_name):
    if model_name == 'logistic_regression':
        models[model_name] = SGDModel()
    else:
        raise ValueError("Model name not recognized.")

def fit(model_name, x, y):
    if model_name in models:
        models[model_name].fit(x, y)
    else:
        raise ValueError("Model not created. Please create the model first.")

def predict(model_name, x):
    if model_name in models:
        return models[model_name].predict(x)
    else:
        raise ValueError("Model not created. Please create the model first.")