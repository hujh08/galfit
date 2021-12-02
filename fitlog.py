#!/usr/bin/env python3

'''
    module to handle fit.log
        a standard output file of galfit

    fit.log contains several logs
        each with information of every galfit running in its directory

    In a log, there are 3 kinds of data:
        starting information:
            input/ouput galfit file, input/output image

        result of optimized parameters:
            values and its uncertainty
            there are also flags to hint state of fitting
                e.g. quoted with '**', meaning unreliable result

        goodness of this fitting:
            chi-square, ndof and chisq/ndof

    3 class in use:
        FitLogs: collection of logs
        FitLog: for one log
        LogMod: for fitting result

    sometimes, only starting information is cared.
        for example, to find output file of last galfit running
    Considering this, the parseing of fitting result could be delayed until needed
        At begining, only lines containg these data is stored
'''

import os
import re

from .collection import inverse_alias
from .dtype import is_int_type, is_str_type, dict_keys_tuple_to_nested

class FitLogs:
    '''
        class for collection of logs
    '''

    # some re pattern to parse fit log
    ## input/output files for galfit running
    strs_files=r'Input image|Init\. par\. file|Restart file|Output image'
    ptn_files=re.compile(r'(%s)\s+:\s+(\S+)' % strs_files)

    ## goodness of fitting, chisq and ndof
    strs_chisqs=r'Chi\^2|ndof|Chi\^2/nu'
    ptn_chisqs=re.compile(r'(%s)\s+=\s+([-+\d\.eE]+)' % strs_chisqs)

    # init
    def __init__(self, path=None, **kwargs):
        '''
            load fit.log to initiate an instance

            Parameters:
                path_log: str or None
                    if None, return an empty instance

                    if str, it means path for a file or dir
                        which is to parse

                kwargs: optional keyword arguments
                    only deliver to method `load_file`
        '''
        self.logs=[]

        if path is not None:
            self.load_file(path, **kwargs)

    ## load fit.log
    def load_file(self, path='', parse_pars=False):
        '''
            load fit.log file

            Parameters:
                path: str for path
                    file or dir

                    if dir, just load fit.log in the dir

                parse_pars: bool
                    whether to parse parameter lines

            a new log is starting when meeting line starting with 'Input image'
        '''
        if os.path.isfile(path):
            filename=path
        elif os.path.isdir(path) or path=='':
            filename=os.path.join(path, 'fit.log')
        else:
            raise Exception('Error: path not exists: [%s]' % str(path))

        # parse file
        with open(filename) as f:
            for line in f:
                line=line.rstrip()
                if not line or line.startswith('-'*10):
                    # ignore lines starting with too many '-'
                    continue

                key_files=self.ptn_files.findall(line)
                if key_files:
                    for k, fname in key_files:
                        if k=='Input image':
                            log=FitLog()
                            self.logs.append(log)

                        log.set_prop_fromlog(k, fname)
                    continue

                key_chisqs=self.ptn_chisqs.findall(line)
                if key_chisqs:
                    for k, val in key_chisqs:
                        log.set_prop_fromlog(k, val)
                    continue

                # append other non-empty line
                log.add_pars_line(line)

        if parse_pars:
            self.parse_pars_lines()

    ## parse parameter lines
    def parse_pars_lines(self):
        '''
            parse parameter lines in all logs
        '''
        for log in self.logs:
            log.parse_pars_lines()

    # get functions
    def get_log_by_index(self, index):
        '''
            get a log by index

            Parameters:
                index: int, slice or other indices object
                    index of logs
        '''
        return self.logs[index]

    def get_logs_by_filename(self, result=None, init=None,
                    index=None, strip=True):
        '''
            get logs by involved galfit file(s)
                that are result and initial files

            return collection or one of matched logs

            Examples:
                fitlogs.get_log_by_filename('galfit.01'):
                    return logs with result file being 'galfit.01'

                fitlogs.get_log_by_filename('galfit.01', 'galfit.00') or
                fitlogs.get_log_by_filename('galfit.01', init='galfit.00'):
                    return logs with result file being 'galfit.01' and
                                     init file 'galfit.00'

                fitlogs.get_log_by_filename('galfit.01', index=-1):
                    return last log with result file 'galfit.01'

            Parameters:
                result, init: str
                    name of galfit result/init file

                index: None, indexing object, str
                    which log to return

                    if None, return all logs as a list
                    if str, only 'all', 'last', 'first', 'newest', 'oldest'

                    for indexing object,
                        it means object which could be used as index of list
                            like int, slice

                strip: bool
                    whether to strip out element from list
                        if only one is contained
        '''
        # at least one filename is given
        assert result is not None or init is not None

        # str index
        if is_str_type(index):
            assert index in ['all', 'last', 'first',
                                    'newest', 'oldest']

            if index=='all':
                index=None

            if index in ['last', 'newest']:
                index=-1
            else:  # first, oldest
                index=0

        # get logs
        logs=self.logs
        if result is not None:
            assert is_str_type(result)
            logs=[l for l in logs if l.result_file==result]
        if init is not None:
            assert is_str_type(init)
            logs=[l for l in logs if l.init_file==init]

        if index is None:
            if strip and len(logs)==1:
                return logs[0]
            return logs

        return logs[index]

    def get_log(self, *args, **kwargs):
        '''
            flexible getter for log
                deliver to other getter based on given arguments

            2 cases:
                just one arg and not str:
                    use get_log_by_index
                otherwise:
                    use get_logs_by_filename
        '''
        if len(args)==1 and not is_str_type(args[0]) and not kwargs:
            return self.get_log_by_index(args[0])

        return self.get_logs_by_filename(*args, **kwargs)

    @property
    def last_log(self):
        '''
            return last log
        '''
        if not self.logs:
            return None

        return self.get_log_by_index(-1)

    ## pack logs to a dict with key being result/init filename
    def get_dict_logs(self, key_style='result', nested=True):
        '''
            return dict of logs
                {key: [log, ...]}

            Parameters:
                key_style: str
                    style of key

                    valid styles:
                        'result', 'init',
                        'result init',
                        'init result'

                nested: bool
                    whether to return nested dict

                    work for multi-layers key,
                        i.e. 'result init' and 'init result'

                    if False, return {(key0, key1): [log, ...]}
                    otherwise, return {key0: {key1: [log, ...]}}
        '''
        assert key_style in {'result', 'init',
                              'result init',
                              'init result'}

        # map the style to attr of `FitLog` object
        map_attrs=dict(result='result_file', init='init_file')

        keynames=key_style.split()
        assert len(keynames)>=1
        # assert all([k in map_attrs for k in keynames])

        keys=[[getattr(log, map_attrs[k]) for log in self.logs]
                for k in keynames]

        if len(keys)==1:
            keys=keys[0]
        else:
            keys=zip(*keys)

        dict_logs=dict(zip(keys, self.logs))

        # nested dict
        if len(keynames)>1 and nested:
            dict_logs=dict_keys_tuple_to_nested(dict_logs)

        return dict_logs

    ## user-friendly functions: to work like list
    def __getitem__(self, prop):
        '''
            magic medthod, user-friendly

            just deliver to `get_log`
        '''
        if isinstance(prop, tuple):
            return self.get_log(*prop)

        return self.get_log(prop)

    ### support len()
    def __len__(self):
        '''
            number of logs
        '''
        return len(self.logs)

class FitLog:
    '''
        class for a log of one galfit running

        3 kinds of data:
            starting information:
                input/ouput galfit file, input/output image

            result of optimized parameters:
                values and its uncertainty
                there are also flags to hint state of fitting
                    e.g. quoted with '**', meaning unreliable result

            goodness of this fitting:
                chi-square, ndof and chisq/ndof

        parsing of fitting result would be delayed until needed
    '''

    # map between key name in fit.log and property in class
    keyname_props=dict(
        input_image=['Input image'],
        output_image=['Output image'],
        init_file=['Init. par. file'],
        result_file=['Restart file'],
        chisq=['Chi^2'],
        ndof=['ndof'],
        reduce_chisq=['Chi^2/nu'],
    )
    map_keyname_props=inverse_alias(keyname_props)

    # init
    def __init__(self):
        '''
            initiation of FitLog
                only to create some properties:
                    input_image, output_image
                    init_file, result_file

                    lines_pars, mods_pars

                    chisq, ndof, reduce_chisq

            such an instance could be created with no input arguments

        '''
        self.input_image=''
        self.output_image=''
        self.init_file=''
        self.result_file=''

        # lines for fitting parameters
        self.lines_pars=[]

        # fitting result. collectin of LogMod instances
        self.mods_pars=[]

        # goodness of fitting
        self.chisq=0
        self.ndof=0
        self.reduce_chisq=0

    # set input/output files of one galfit running
    def set_prop_fromlog(self, key, val):
        '''
            set log property from (key, val) pair in fit.log
                including: files information and chisqs

            Parameters:
                key: key name in starndard fit.log file
        '''
        assert key in self.map_keyname_props

        prop=self.map_keyname_props[key]

        # float value for chisq
        if prop in {'chisq', 'reduce_chisq'}:
            val=float(val)
        elif prop=='ndof':
            val=int(val)

        # set
        setattr(self, prop, val)

    # add par line
    def add_pars_line(self, line):
        '''
            add line for fitting result of component parameters
        '''
        self.lines_pars.append(line)

    # parse parameter lines
    def parse_pars_lines(self):
        '''
            parse lines of components parameters, `lines_pars`
        '''
        lines=self.lines_pars
        assert len(lines) % 2 == 0  # must exist in pairs

        for line_val, line_uncert in zip(lines[0::2], lines[1::2]):
            self.mods_pars.append(LogMod(line_val, line_uncert))

class LogMod:
    '''
        class for fitting result of one component
    '''
    # re pattern for an item in line of values or uncertainties
    item_ends='][()*,}{'
    ptn_item=re.compile(r'^([{0}]*)([^{0}]*)([{0}]*)$'.format(item_ends))

    # init
    def __init__(self, *lines, name=''):
        '''
            initiate LogMod with two lines
                one for values and another for uncertainties
        '''
        self.name=name  # component name
        self.vals=[]
        self.uncerts=[]
        self.flags=[]

        if lines:
            self.load_lines(*lines)

    def load_lines(self, line_val, line_uncert):
        '''
            load two lines to set the instance
                for values and uncertainties respectively

            values, uncertainties and flags of parameters
                are extracted from these two lines
        '''
        self.load_line_val(line_val)
        self.load_line_uncert(line_uncert)

        if not len(self.vals)==len(self.uncerts)==len(self.flags):
            raise Exception('mismatch of number after line-parse')

    def load_line_val(self, line):
        '''
            parse line of values

            values and flags are extracted
        '''
        name, vals=line.split(':', maxsplit=1)
        self.name=name.strip().lower()

        for field in vals.split():
            val, flag=self.parse_item(field)
            if val==None:
                continue
            self.vals.append(val)
            self.flags.append(flag)

        # ignoring first two items for model sky, which are center of image
        if self.name=='sky':
            self.vals[:2]=[]
            self.flags[:2]=[]

    def load_line_uncert(self, line):
        '''
            parse line of uncertainties

            only extract uncertainties
                ignoring flags
        '''
        for field in line.split():
            val, flag=self.parse_item(field)
            if val==None:
                continue
            self.uncerts.append(val)

    def parse_item(self, item):
        '''
            parse an item in line of values or uncertainties

            return (value, flag)
        '''
        m=self.ptn_item.match(item)
        if not m:
            return None, None

        groups=m.groups()
        if not groups[1]:
            return None, None

        val=float(groups[1])

        flag='normal'
        head, tail=groups[0], groups[2]
        if head and tail:
            mark=head[-1]+tail[0]
            if mark==r'**':
                flag='unreliable'
            elif mark==r'[]':
                flag='fixed'
            elif mark==r'{}':
                flag='constrainted'

        return val, flag
