# module for mask

from .mask import RegMask
from .io import *

def load_reg(fname):
    return RegMask(fname)