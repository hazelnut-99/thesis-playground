from river import tree, ensemble, preprocessing, linear_model, drift
import numpy as np
import random

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

class HoeffdingTreeAdaptiveModel:
    def __init__(self):
        self.model = tree.HoeffdingAdaptiveTreeClassifier(
            grace_period=100,
            delta=1e-5,
            leaf_prediction='nb',
            nb_threshold=10,
            seed=RANDOM_SEED,
        )

    def fit(self, x1, x2, y):
        x_dict = {'f1': x1, 'f2': x2}
        self.model.learn_one(x_dict, y)
    
    def predict(self, x1, x2):
        return self.model.predict_one({'f1': x1, 'f2': x2})


class LeveragingBaggingModel:
    def __init__(self):
        self.model = ensemble.LeveragingBaggingClassifier(
            model=(
                preprocessing.StandardScaler() |
                linear_model.LogisticRegression()
            ),
            seed=RANDOM_SEED,
        )

    def fit(self, x1, x2, y):
        x_dict = {'f1': x1, 'f2': x2}
        self.model.learn_one(x_dict, y)
    
    def predict(self, x1, x2):
        return self.model.predict_one({'f1': x1, 'f2': x2})


class KSWINDriftDetector:
    def __init__(self):
        self.detector = drift.KSWIN(alpha=0.005, seed=RANDOM_SEED)
    
    def check(self, x):
        self.detector.update(x)
        return 1 if self.detector.drift_detected else 0