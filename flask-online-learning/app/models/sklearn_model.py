from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.exceptions import NotFittedError
import numpy as np
import random

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

class SGDModel:
    def __init__(self):
        self.model = SGDClassifier(loss='log_loss', random_state=RANDOM_SEED, class_weight={0: 3, 1: 1})

    def fit(self, x1, x2, y):
        if self.model is None:
            raise NotFittedError("Model is not created. Call create_model first.")
        self.model.partial_fit([[x1, x2]], [y], classes=[0, 1])

    def predict(self, x1, x2):
        if self.model is None:
            raise NotFittedError("Model is not created. Call create_model first.")
        return self.model.predict([[x1, x2]])[0]