import tensorflow as tf
from keras.models import load_model
import numpy as np
import os.path


BASE = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(BASE, "ann_one_hot.h5")

def predictWinRate(radianceIds, direIds):
    with tf.Session():
        print("Radiance Heroes: ", radianceIds, "Type: ", type(radianceIds[0]), "\nDire Heroes: ", direIds)
        classifier = load_model(model)
        X_test1 = [0.,1.,0.] * 113 + [1.]
        for i in radianceIds:
            j = i - 1 if i < 24 else i - 2
            X_test1[j*3+1] = 0.
            X_test1[j*3+2] = 1.
        for i in direIds:
            j = i - 1 if i < 24 else i - 2
            X_test1[j*3+1] = 0.
            X_test1[j*3] = 1.

        X_test1 = X_test1[:69] + [1.] + X_test1[69:]
        X_test1 = np.array([X_test1])
        prediction = list(classifier.predict_proba(X_test1))
        return prediction[0][0]
