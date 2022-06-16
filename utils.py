from typing import Type
import numpy as np

def base_to_list(n, base=10):
    result = []
    n = int(n)
    while(n):
        result.append(n%base)
        n //= base
    result.reverse()
    return result

def list_to_str(l):
    l = ""
    for each in l:
        l += str(l)
    return l
    
def stereo_sound(left, right, left_volume=1.0, right_volume=1.0):
    return np.column_stack([left*left_volume, right*right_volume])

def is_iterable(x):
    try:
        x.__iter__
        return True
    except AttributeError:
        return False
    