#!/usr/bin/env python3

'''
    class for a fitting parameter
        with property val, state, uncertainty (optional)
'''

from .dtype import is_str_type, is_int_type, is_vec_type, is_number_type

class Parameter:
    '''
        class of fitting parameter

        3 main property: val, state, uncertainty
            val: value of the parameter
            state: fitting state
                whether the parameter is free (1) or freeze (0) to fit
            uncert: uncertainty of fitting result
                optional
    '''
    FREE=1
    FREEZE=0

    map_vals={'free': FREE, 'freeze': FREEZE}

    # __slots__=['val', 'state', 'uncert']  # allocate a static amount of memory

    def __init__(self, *args):
        '''
            initiation of parameter

            only allow 1,2,3 arguments
                1-arg: str, vector, or number
                    if str, split and analysis agian
                2-args: val, state
                    val: str, or numbers
                    state: str, or int
                3-args: val, state, uncertainty
                    uncertainty: optional, None, str, or numbers
        '''
        # set default state, uncert
        self.set_state()
        self.set_uncert()

        # parse args
        assert args  # at least one argument
        self.update(*args)

    # determine function
    def is_frozen(self):
        return self.state==self.FREEZE

    def is_free(self):
        return not self.is_frozen()

    # basic methods to set: val, state, uncert
    def set_val(self, v):
        '''
            set property `val`
        '''
        self.__dict__['val']=float(v)

    def set_state(self, v=0):
        '''
            set property `val`

            only allow int, str
                for str, it could be str of int, or a key to a value
        '''
        assert is_int_type(v) or is_str_type(v)
        
        if is_str_type(v):
            if v in self.map_vals:
                v=self.map_vals[v]
            else:
                v=int(v)

        self.__dict__['state']=int(v)

    def set_uncert(self, v=None):
        '''
            set property `uncert`

            None or float
        '''
        if v is not None:
            v=float(v)
        self.__dict__['uncert']=v

    ## frequently used
    def free(self):
        self.set_state(self.FREE)

    def freeze(self):
        self.set_state(self.FREEZE)

    ## flexible update
    def update(self, *args, **kwargs):
        '''
            flexible way to update

            like:
                update(val, [state, [uncert]])
                # update({val=..., state=..., ...}) # deprecated
                update(val=..., state=..., ...)
        '''
        if len(args)==1:
            v=args[0]
            if is_str_type(v):
                args=v.split()
                if len(args)!=1: # maybe empty string
                    return self.update(*args, **kwargs)
            elif isinstance(v, type(self)):
                return self.update(v.val, v.state, v.uncert, **kwargs)
            elif is_vec_type(v):
                return self.update(*v, **kwargs)
            # elif isinstance(v, dict):
            #     return self.update(**v, **kwargs)
        elif len(args)>3:
            raise Exception('only allow 0-3 arguments, got %i' % (len(args)))

        if args:
            keys=['val', 'state', 'uncert']  # order for args
            for k, v  in zip(keys, args):
                if k in kwargs:
                    raise Exception('conflict arguments for '+k)
                kwargs[k]=v

        # update kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    ## state operation
    @classmethod
    def state_of_comb_pars(cls, p0, p1):
        '''
            state of a parameter by combing two pars

            `p0`, `p1` could be instance, or state
        '''
        if isinstance(p0, cls):
            p0=p0.state
        if isinstance(p1, cls):
            p1=p1.state

        return int(bool(p0+p1))

    ## intercept other setting
    def __setattr__(self, prop, val):
        props_valid={'val', 'state', 'uncert'}
        if prop not in props_valid:
            raise Exception('only allow properties: %s, but got \'%s\''
                                % (str(props_valid), prop))

        getattr(self, 'set_'+prop)(val)

    ## copy
    def copy(self):
        '''
            copy as a new instance
        '''
        return type(self)(self)

    # string representation
    def str_val(self):
        '''
            str of val
        '''
        if abs(self.val)<1e-3:
            return '%.3e' % self.val
        else:
            return '%.4f' % self.val

    def __str__(self):
        '''
            user-friendly string representation
        '''
        s=self.str_val()
        return '%-11s %i' % (s, self.state)

    def __repr__(self):
        '''
            developer-friendly
        '''
        ss='%g, %i' % (self.val, self.state)
        if self.uncert is not None:
            ss+=', %g' % self.uncert

        name=self.__class__.__name__
        return '%s(%s)' % (name, ss)

    # reload numerical operator
    def _gen_inplace_op(self, v, f):
        '''
            general method for inplace operation

            Parameter:
                v: str, number, instance of Parameter

                    for instance of Parameter, only use the prop `val`

                f: callable
                    accept `self.val` and v as arguments
                    and return a value back set to `self.val`
        '''
        assert is_number_type(v) or is_str_type(v) or isinstance(v, type(self))

        # convert to Parameter instance for str
        if is_str_type(v):
            return self.__iadd__(type(self)(v))

        # only use the val for Parameter instance
        if isinstance(v, type(self)):
            v=v.val

        self.set_val(f(self.val, v))

        return self

    def __iadd__(self, v):
        '''
            inplace add

            see `_gen_inplace_op` for detail
        '''
        return self._gen_inplace_op(v, lambda x, y: x+y)

    def __imul__(self, v):
        '''
            inplace multiply

            arguments and treatment to Parameter instance
                same as `__iadd`
        '''
        return self._gen_inplace_op(v, lambda x, y: x*y)
