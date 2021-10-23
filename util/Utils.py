import math


def isBad(val):
    """
    Checks for nan/None
    :return:
    """
    if val is None:
        return True
    if math.isnan(val):
        return True
    return False
