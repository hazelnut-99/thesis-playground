from flask import Blueprint, request, jsonify
from app.models.sklearn_model import SGDModel
from app.models.river_model import HoeffdingTreeAdaptiveModel, LeveragingBaggingModel, KSWINDriftDetector

bp = Blueprint('api', __name__)

models = {}

@bp.route('/create_model', methods=['POST'])
def create_model():
    model_name = request.json.get('model_name')
    model_type = request.json.get('model_type')

    if model_name in models:
        return jsonify({'error': 'Model already exists'}), 400

    if model_type == 'SGD':
        models[model_name] = SGDModel()
    elif model_type == 'HDT':
        models[model_name] = HoeffdingTreeAdaptiveModel()
    elif model_type == 'LB':
        models[model_name] = LeveragingBaggingModel()
    else:
        return jsonify({'error': 'Invalid model type'}), 400

    return jsonify({'message': f'Model {model_name} created successfully'}), 201

@bp.route('/fit', methods=['POST'])
def fit():
    model_name = request.json.get('model_name')
    x1 = request.json.get('x1')
    x2 = request.json.get('x2')
    y = request.json.get('y')

    if model_name not in models:
        return jsonify({'error': 'Model not found'}), 404

    models[model_name].fit(x1, x2, y)
    return jsonify({'message': f'Model {model_name} fitted successfully'}), 200

@bp.route('/predict', methods=['POST'])
def predict():
    model_name = request.json.get('model_name')
    x1 = request.json.get('x1')
    x2 = request.json.get('x2')

    if model_name not in models:
        return jsonify({'error': 'Model not found'}), 404

    y_pred = int(models[model_name].predict(x1, x2))
    return jsonify({'predictions': y_pred}), 200


@bp.route('/create_detector', methods=['POST'])
def create_model():
    model_name = request.json.get('model_name')

    if model_name in models:
        return jsonify({'error': 'Model already exists'}), 400
    models[model_name] = KSWINDriftDetector()
    return jsonify({'message': f'Model {model_name} created successfully'}), 201


@bp.route('/detect', methods=['POST'])
def predict():
    model_name = request.json.get('model_name')
    x = request.json.get('x')

    if model_name not in models:
        return jsonify({'error': 'Model not found'}), 404

    y_pred = int(models[model_name].check(x))
    return jsonify({'predictions': y_pred}), 200
