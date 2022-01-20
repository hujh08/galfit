# module for mask

from .mask import RegMask

def load_reg(fname):
    return RegMask(fname)