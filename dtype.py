#!/usr/bin/env python3

'''
    functions for data type
'''

import numbers

# determine function
def is_number_type(val):
    '''
        determine whether a data is number
    '''
    return isinstance(val, numbers.Number)

def is_float_type(val):
    '''
        determine whether a data is float
    '''
    return isinstance(val, numbers.Real) and not isinstance(val, numbers.Integral)

def is_int_type(val):
    '''
        determine whether a data is int
    '''
    return isinstance(val, numbers.Integral)

def is_str_type(val):
    '''
        determine whether a data is str
    '''
    return isinstance(val, str)

def is_vec_type(val):
    '''
        determine whether data could be treated as vector

        Current type as a vector
            list
            tuple
    '''
    return isinstance(val, list) or isinstance(val, tuple)
