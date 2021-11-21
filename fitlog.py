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

from .collection import inverse_alias, is_int_type

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
    def __init__(self, filename=None, **kwargs):
        '''
            load fit.log to initiate an instance

            optional kwargs are used in `load_file`. see `load_file` for detail
            some important arguments:
                dir_log: directory for the log
        '''
        self.logs=[]

        if filename:
            self.load_file(filename, **kwargs)

    ## load fit.log
    def load_file(self, filename='fit.log', dir_log=None, parse_pars=False):
        '''
            load fit.log file

            Parameters:
                dir_log: directory of the log

                parse_pars: bool
                    whether to parse parameter lines

            a new log is starting when meeting line starting with 'Input image'
        '''
        if dir_log is not None:
            filename=os.path.join(dir_log, filename)

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

    # fetch functions
    def get_log(self, prop):
        '''
            fetch a log
        '''
        if is_int_type(prop):
            return self.logs[prop]

        raise Exception('unexpected type of prop: %s' % type(prop).__name__)

    @property
    def last_log(self):
        '''
            return last log
        '''
        if not self.logs:
            return None

        return self.logs[-1]

    ## user-friendly functions: to work like list
    def __getitem__(self, prop):
        '''
            magic medthod, user-friendly
        '''
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
