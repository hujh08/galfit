#!/usr/bin/env python3

'''
    Module to handle constraint file
'''

import re

from .collection import inverse_alias
from .dtype import is_str_type, is_int_type

class Constraints:
    '''
        class to represent a constraint file
            that is collection of serveral constraint rules,

        A constraint rule in the collection is represented by class `ConsRule`
    '''
    def __init__(self, fname=None):
        '''
            initiation

            it could be initiated as empty, if `fname` is None
                or to load a constraint file

            Parameter
                fname: None, or str
                    for str, if it is 'none', same as None
        '''
        self.rules_cons=[]   # collection of constraints

        assert fname is None or is_str_type(fname)

        if is_str_type(fname) and fname!='none':
            self.load_file(fname)

    def load_file(self, fname):
        '''
            load a constraint file
        '''
        with open(fname) as f:
            for line in f:
                line=line.strip()
                if (not line) or line[0]=='#':
                    continue
                self.add_cons(line)

    ## add method
    def add_cons(self, *args):
        '''
            add a constraint rule from a line or other arguments

            2 kinds of arguments allowed:
                1 argument: line in galfit constraint file
                3-4 argumens: comps, par, type_cons[, range]
            see `ConsRule.__init__` for detail
        '''
        self.rules_cons.append(ConsRule(*args))

    ### frequently used functions
    def add_hard_cons_position(self, comps, p):
        '''
            add hard constraint to position parameters, like x, y

            constraint type: hard_offset
        '''
        self.add_cons(comps, p, 'hard_offset')

    def add_hard_cons_to_xy(self, *comps):
        '''
            add hard_offset constraint to xy parameters

            frequently used for fitting with homocentric components,
                like homocentric bulge/disk
        '''
        self.add_cons(comps, 'x', 'hard_offset')
        self.add_cons(comps, 'y', 'hard_offset')

    def add_range_to_par(self, comp, p, minmax):
        '''
            constrain a parameter to a range `minmax`

            constraint type: soft_fromto

            :argument comp must be a integral
        '''
        assert is_int_type(comp)
        self.add_cons([comp], p, 'soft_fromto', minmax)

    def add_relrange_to_par(self, comp, p, minmax):
        '''
            constrain a parameter to a relative range `minmax`

            constraint type: soft_shift

            :argument comp must be a integral
        '''
        assert is_int_type(comp)
        self.add_cons([comp], p, 'soft_shift', minmax)

    # stringlizing
    def __str__(self):
        '''
            user-friendly string
        '''
        return '\n'.join(map(str, self.rules_cons))

    def writeto(self, fname):
        '''
            write to a file
        '''
        with open(fname, 'w') as f:
            f.write(str(self)+'\n')

    # magic method
    def __len__(self):
        '''
            number of rules
        '''
        return len(self.rules_cons)

class ConsRule:
    '''
        class for one constraint rule

        6 types of constraint
            hard, offset: e.g. '1_2_3   x   offset'
                keep x1-x2, x2-x3 fixed during fitting
                    x1,x2,x3 for parameter x of components 1,2,3
                often used for position parameters, like center x, y

            hard, ratio: e.g. '1_2_3   r   ratio'
                keep r1/r2, r2/r3 fixed during fitting
                often used for positive parameters, like re, ba

            soft, fromto range: e.g. '1    n   v1 to v2'
                keep n1 within values from v1 to v2
                often used for values having empirical range, like sersic index

            soft, shift range: e.g. '1    x   d1  d2'
                keep shift x within range from v1 to v2
                    that is, assume x0 now,
                        then x must be from x0+d1 to x0+d2 during fitting
                often used for values having a varing range

            soft, offset range: e.g. '1-2    x    v1 v2'
                keep x1-x2 within values from v1 to v2

            soft, ratio range: e.g. '1/2    r    t1 t2'
                keep r1/r2 within values from v1 to v2

        2 ways to construct a constraint rule
            -- ConsRule(line)
                line is of the format in galfit constraint file

            -- ConsRule(comps, par, type_cons[, range])
                range is only required for soft constraint
    '''
    # re pattern
    fmt_ptn=r'^\s*(%s)\s+([a-zA-Z\d]+)\s+(%s)(?:\s*$|\s+#)'

    ## hard offest
    fmt_comps=r'\d+_\d+(?:_\d+)*'
    ptn_offset=re.compile(fmt_ptn % (fmt_comps, 'offset'))

    ## hard ratio
    ptn_ratio=re.compile(fmt_ptn % (fmt_comps, 'ratio'))

    ## soft, from to: v1 to v2, constraining values within v1 to v2
    fmt_flt=r'[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?'  # float
    fmt_cons_to=r'({0})\s+to\s+({0})'.format(fmt_flt)
    ptn_fromto=re.compile(fmt_ptn % (r'\d+', fmt_cons_to))

    ## soft, shift: v1 v2, (current v), constraining values v+v1 to v+v2
    fmt_cons_range=r'({0})\s+({0})'.format(fmt_flt)
    ptn_shift=re.compile(fmt_ptn % (r'\d+', fmt_cons_range))

    ## soft, offset: p1-p2 x v1 v2
    ptn_soft_offset=re.compile(fmt_ptn % (r'\d+-\d+', fmt_cons_range))

    ## soft, ratio: p1/p2 x v1 v2
    ptn_soft_ratio=re.compile(fmt_ptn % (r'\d+/\d+', fmt_cons_range))

    ### collections of pattern
    ptns_cons=dict(
        hard_offset=ptn_offset,
        hard_ratio=ptn_ratio,
        soft_fromto=ptn_fromto,
        soft_shift=ptn_shift,
        soft_offset=ptn_soft_offset,
        soft_ratio=ptn_soft_ratio,
    )

    # constraint type
    types_cons_valid=set(ptns_cons.keys())

    # alias of constraint type
    alias_types_cons=dict(
        hard_offset=['hard_diff'],
        # hard_ratio=[],
        # soft_fromto=[],
        soft_shift=['soft_vary'],
        soft_offset=['soft_diff'],
        # soft_ratio=[],
    )
    map_alias_types=inverse_alias(alias_types_cons)

    # seperation of components: mainly used for output
    seps_cons=dict(
        hard_offset='_',
        hard_ratio='_',
        soft_fromto='',
        soft_shift='',
        soft_offset='-',
        soft_ratio='/',
    )

    def __init__(self, *args):
        '''
            3 properties for a constraint rule
                comps: components containing parameters with constraint
                    index of components starts from 1, not 0
                par: parameter with constraint
                vals: constraint type
                    `vals` has format (type_cons[, range])
                        where range is only required for soft constraint

            arguments to initiate an instance
                1 argument: line in galfit constraint file

                3-4 argumens: comps, par, type_cons[, range]
        '''
        self.comps=[]
        self.par=''

        # type of constraint: hard_{offset,ratio}, soft_{fromto,shift,offset,ratio}
        self.type_cons=''
        self.range_cons=[]   # range of constraint, only required for soft type

        if len(args)==1:
            self.load_line(args[0])
        elif len(args)==3 or len(args)==4:
            self.set_cons(*args)
        else:
            raise Exception('only allow 1,3,4 argumens. But got %i' % len(args))

    # set functions
    def set_type_cons(self, t):
        '''
            set type of constraint

            bottom function

            alias of constraint name is supported
        '''
        if t in self.map_alias_types:
            t=self.map_alias_types[t]
        
        assert t in self.types_cons_valid
        self.type_cons=str(t)

    def set_cons(self, comps, par, type_cons, range_cons=None):
        '''
            set a constraint rule

            bottom function.
                other setter, like `load_line`, would call it

            Parameter:
                comps: indices of components to constrain

                par: parameter to constrain

                type_cons: type of constraint
                    6 types: hard_{offset,ratio},
                             soft_{fromto,shift,offset,ratio}

                range_cons: range of constraint
                    optional, only required for soft constraint

            validity of arguments are also checked
        '''
        # type of constraint
        self.set_type_cons(type_cons)

        # comps
        self.comps=[int(i) for i in comps]

        ## check number of comps
        n=self.num_comps_req_of_cons()
        if n is not None:
            assert n==len(self.comps)

        # par
        assert is_str_type(par)
        self.par=str(par)

        # range of constraint
        if self.is_soft_cons():
            assert len(range_cons)==2
            self.range_cons=[float(i) for i in range_cons]

    def load_line(self, line):
        '''
            load a line in constraint file
        '''
        line=line.strip()

        if (not line) or line[0]=='#':
            return

        for t, ptn in self.ptns_cons.items():
            m=ptn.match(line)
            if m:
                break

        if not m:
            return

        comps, par, *vals=m.groups()

        s=self.seps_cons[t]
        if s:
            comps=[int(i) for i in comps.split(s)]
        else:
            comps=[int(comps)]

        args=[t]  # argument to set to constraint
        if self.is_soft_cons(t):
            args.append([float(i) for i in vals[-2:]])

        self.set_cons(comps, par, *args)

    # functions about constraint type
    def is_soft_cons(self, t=None):
        '''
            to determine whether a type or the instance self is soft constraint
        '''
        if t is None:
            t=self.type_cons

        return t.startswith('soft_')

    def num_comps_req_of_cons(self, t=None):
        '''
            required number of components for a constraint or self

                if no requirement, return None

            3 kinds:
                hard_{offset,ratio}: no requirement

                soft_{fromto,shift}: 1

                soft_{offset,ratio}: 2
        '''
        if t is None:
            t=self.type_cons

        if not self.is_soft_cons(t):
            return None

        if t[len('soft_'):] in {'fromto', 'shift'}:
            return 1

        # else: soft_{offset,ratio}
        return 2


    # stringlizing
    def __str__(self):
        '''
            string of the constraint rule
        '''
        if not self.comps:
            return ''

        fmt='%s    %s    %s' # format of the string

        # parameter
        par=self.par

        # componentss
        t=self.type_cons
        comps=self.seps_cons[t].join(map(str, self.comps))

        # constraint values
        if t.startswith('hard_'):
            vals=t[len('hard_'):]
        else:
            if t=='soft_fromto':
                fmt_v='%g to %g'
            else:
                fmt_v='%g %g'
            vals=fmt_v % tuple(self.range_cons)

        return fmt % (comps, par, vals)


