#!/usr/bin/env python3

'''
    module to emulate numeric type
        like float
'''

# auxiliary functions
def get_func_for_op(op, t_num, nargs, assign=False):
    '''
        return function as the method correpsond to operand

        To emulate an numeric type, e.g. float, int
            it is necessary to define the method
                which returns a value of appropriate type
            for example, __float__ for float type
        Then operands would be implemented
            by just delivering to the returned value of this method
        Using __add__ and float as example, it could be
            lambda self, v: float(self).__add__(v)

        For augumented arithmetic assignment, like += (method __iadd__)
            a method `_assign_to` should be defined,
                which should return object-self
                    since variant linked would be assign to
                        returned value of the method
            and correponding operand, like __add__ for __iadd__
                should be already implemented
        Then this assignment could be implemented as, using __iadd__ as example,
            lambda self, v: self._assign_to(self.__add__(v))

        Parameter:
            op: str
                method name for an operand
                    e.g. __add__, __radd__

            t_num: type
                numeric type to emulate
                    e.g. float, int

            nargs: int, only 1 or 2
                num of args for the operand
                only allow 1 or 2

            assign: bool
                whether to implement assignment method
                    e.g. __iadd__
                if True, `op` should be the basic operand
                    for example, __add__ for __iadd__
    '''
    assert nargs==1 or nargs==2

    if assign:
        assert nargs==2
        return lambda self, v: self._assign_to(getattr(self, op)(t_num(v)))

    if nargs==1:
        return lambda self: getattr(t_num(self), op)()
    else:
        return lambda self, v: getattr(t_num(self), op)(t_num(v))

def add_opfuncs_to(dict_vars, t_num, ops_comp=None,
                    ops_binary=None, ops_unary=None,
                    fmt_doc='emulate {1} {0}'):
    '''
        add magic methods for operands
            to dict of vars, like locals()

        Parameters:
            dict_vars: dict
                dest dict to add

            t_num: type
                numeric type to emulate

            ops_binary, ops_unary, ops_comp: list of str, None
                binary, unary and comparison operands

                if None, use default methods
                    that are
                        ops_binary: add sub mul truediv pow
                        ops_unary:  neg pos abs
                        ops_comp:   lt gt le ge eq ne

            fmt_doc: python style format string
                format of doc of implemented methods

                it is used by FMT_DOC.format(t, tname)
                    where t:     method name and
                          tname: numeric type name
    '''
    tname=t_num.__name__

    # confirm necessary method for operands, e.g. __float__
    assert '__{}__'.format(tname) in dict_vars

    # default operands
    if ops_binary is None:
        ops_binary='add sub mul truediv pow'.split()

    if ops_unary is None:
        ops_unary='neg pos abs'.split()

    if ops_comp is None:  # comparison methods
        ops_comp='lt gt le ge eq ne'.split()

    fmts=['__{}__', '__r{}__']
    for ops, nv, ifmts in [(ops_unary, 1, fmts[:1]),
                           (ops_comp, 2, fmts[:1]),
                           (ops_binary, 2, fmts)]:
        for op in ops:
            for fmt in ifmts:
                t=fmt.format(op)
                f=get_func_for_op(t, t_num, nv)
                f.__doc__=fmt_doc.format(t, tname)

                dict_vars[t]=f

    # augmented arithmetic assignments
    assert '_assign_to' in dict_vars
    for op in ops_binary:
        t0='__{}__'.format(op)
        t='__i{}__'.format(op)

        f=get_func_for_op(t0, t_num, 2, assign=True)
        f.__doc__=fmt_doc.format(t, tname)

        assert t0 in dict_vars
        dict_vars[t]=f

# basic class
class MockFLT:
    '''
        mock class for float type
    '''
    def __float__(self):
        '''
            necessary to emulate float
        '''
        return NotImplemented

    def _assign_to(self, v):
        '''
            necessay to augmented arithmetic assignments
        '''
        return NotImplemented

    add_opfuncs_to(locals(), float)