from __future__ import absolute_import, print_function, division, unicode_literals
import imp
import sys
import os
import hashlib
import numpy as np
from six import exec_
from sklearn.datasets import load_iris
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score


def hash_file(path, block_size=65536):
    """Returns SHA256 checksum of a file

    Args:
        path (string): Absolute file path of file to hash

        block_size (int, optional): Number of bytes to read per block
    """
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()


def hash_string(string):
    """Hashes an input string using SHA256"""
    return hashlib.sha256(string).hexdigest()


def import_object_from_path(path, object):
    """Used to import an object from an absolute path.

    This function takes an absolute path and imports it as a Python module.
    It then returns the object with name `object` from the imported module.

    Args:
        path (string): Absolute file path of .py file to import

        object (string): Name of object to extract from imported module
    """
    with open(path) as f:
        return import_object_from_string_code(f.read(), object)


def import_object_from_string_code(code, object):
    """Used to import an object from arbitrary passed code.

    Passed in code is treated as a module and is imported and added
    to `sys.modules` with its SHA256 hash as key.

    Args:
        code (string): Python code to import as module

        object (string): Name of object to extract from imported module
    """
    sha256 = hashlib.sha256(code).hexdigest()
    module = imp.new_module(sha256)
    exec_(code, module.__dict__)
    sys.modules[sha256] = module
    return getattr(module, object)


def verify_dataset_extraction_function(function):
    """Verify a dataset extraction function

    Used to verify a dataset extraction function by returning shape and basic
    statistics of returned data. This will also provide quick and dirty check
    on capability of host machine to process the data

    Args:
        function (callable): Main dataset extraction function to test

    Returns:
        X_shape (2-tuple of int): Shape of X returned

        y_shape (1-tuple of int): Shape of y returned

    Raises:
        AssertionError: `X_shape` must be of length 2 and `y_shape` must be of
            length 1. `X` must have the same number of elements as `y`
            i.e. X_shape[0] == y_shape[0]. If any of these conditions are not met,
            an AssertionError is raised.
    """
    X, y = function()
    X_shape, y_shape = np.array(X).shape, np.array(y).shape
    assert len(X_shape) == 2
    assert len(y_shape) == 1
    assert X_shape[0] == y_shape[0]
    return X_shape, y_shape


def verify_estimator_class(cls, **params):
    """Verify an estimator class by testing its performance on Iris

    Verification of essential methods for xcessiv is also done using
    `hasattr`.

    Args:
        cls (class): Estimator class with `fit`, `predict`/`predict_proba`,
            `get_params`, and `set_params` methods.

        params (mapping): Dictionary used to set parameters of the
            estimator.

    Returns:
        performance_dict (mapping): Mapping from performance metric
            name to performance metric value e.g. "Accuracy": 0.963
    """
    X, y = load_iris(return_X_y=True)

    if not params:
        clf = cls()  # Use default params
    else:
        clf = cls().set_params(**params)

    assert hasattr(clf, "get_params")
    assert hasattr(clf, "set_params")

    performance_dict = dict()
    performance_dict['has_predict_proba'] = hasattr(clf, 'predict_proba')
    performance_dict['has_decision_function'] = hasattr(clf, 'decision_function')

    true_labels = []
    preds = []
    for train_index, test_index in StratifiedKFold().split(X, y):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        clf.fit(X_train, y_train)
        true_labels.append(y_test)
        preds.append(clf.predict(X_test))
    true_labels = np.concatenate(true_labels)
    preds = np.concatenate(preds)
    performance_dict['Accuracy'] = accuracy_score(true_labels, preds)

    return performance_dict
