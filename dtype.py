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

# function for convert of collection types
def dict_keys_tuple_to_nested(d, keep_nontup_key=True):
    '''
        convert dict with keys of type tuple
            to one with nested key

        For example
            tuple key: {(k0, k1): val}
            nested key: {k0: {k1: val}}

        Parameters:
            d: dict
                original data

            keep_nontup_key: bool
                whether to keep entries
                    for a non-tuple key
    '''
    assert isinstance(d, dict)

    # to nested key
    result={}
    for tupks, v in d.items():
        if not isinstance(tupks, tuple):
            if keep_nontup_key:
                assert tupks not in result
                result[tupks]=v
            continue

        d=result
        for k in tupks[:-1]:
            if k not in d:
                d[k]={}
            d=d[k]

        k=tupks[-1]
        assert k not in d
        d[k]=v

    return result