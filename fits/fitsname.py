#!/usr/bin/env python3

'''
    function to parse extended FITS file name
'''

import re

# pattern for file name
fmt_sqbra=r'\[\s*({0})\s*\]'  # enclosed in square brackets

## section
ptn_int=re.compile(r'[-+]?\d+')
ptn_slice=re.compile(r'(?:(-?\*)|({0}):({0}))(?::({0}))?'.format(ptn_int.pattern))
ptn_sect=re.compile(r'{0}(?:\s*,\s*{0})*'.format(ptn_slice.pattern))
ptn_syn_sect=re.compile(fmt_sqbra.format(ptn_sect.pattern))  # with square bracket

## HDU
ptn_xten=re.compile(r'IMAGE|ASCII|TABLE|BINTABLE|I|A|T|B')
ptn_extname=re.compile(r'([^,]+)(?:{0}(\d+))?(?:{0}({1}))?'.format(r'\s*,\s*', ptn_xten.pattern))
ptn_hdu=re.compile(r'({0})|({1})'.format(ptn_int.pattern, ptn_extname.pattern),
                    flags=re.IGNORECASE)
ptn_syn_hdu=re.compile(fmt_sqbra.format(ptn_hdu.pattern), flags=re.IGNORECASE)

## extended file name
ptn_extfname=re.compile(r'(?P<fname>.*?)(?P<hdu>{0})?\s*'
                        r'(?P<sect>{1})?\s*'.format(ptn_syn_hdu.pattern,
                                                     ptn_syn_sect.pattern),
                            flags=re.IGNORECASE)

# parser of extended file name
def parse_ext_fitsname(fitsname):
    '''
        parse an extended file name

        return fitsname, hdu ext, image section
        if any not specified, use None
            
            -fitsname: name of the FITS file in system

            -hdu ext:  two types to return:
                int: extno
                3-tuple: extname, extver, xtension
                    extver, xtension be None if not exist

            -image section: slice in image
                e.g. x0:x1[:dx]

    '''
    # '.*' exists in ptn_extfname, it would match every string
    dict_fhs=ptn_extfname.fullmatch(fitsname).groupdict()

    fname=dict_fhs['fname']
    hdu=dict_fhs['hdu']
    sect=dict_fhs['sect']

    # hdu
    if hdu is not None:
        hdu=ext_dict_hdu(hdu)

    # image section
    if sect is not None:
        sect=ext_slices_sect(sect)

    # return
    return fname, hdu, sect

## ext dict of hdu
def ext_dict_hdu(s):
    '''
        extract a information for hdu

        two types to return:
            extno
            extname, extver, xtension
                where extver, xtension could be None if not existed
    '''
    m=ptn_syn_hdu.fullmatch(s)
    if not m:
        return None

    fields=m.groups()

    # extno
    if fields[1] is not None:
        return int(fields[1])

    # extname
    extname, extver, xtension=fields[-3:]
    assert extname is not None

    d=dict(extname=extname)
    
    ## extver
    if extver is not None:
        extver=int(extver)

    ## xtension
    if xtension is not None:
        xtension=normal_xtension(xtension)

    return extname, extver, xtension

### normalize xtension
def normal_xtension(x):
    '''
        normalize xtension

        upper case
        IMAGE, ASCII, TABLE, BINTABLE
    '''
    x=x.upper()

    if len(x)==1:
        map_abbr=dict(I='IMAGE', T='TABLE', A='ASCII', B='BINTABLE')
        x=map_abbr[x]
    else:
        assert x in {'IMAGE', 'TABLE', 'ASCII', 'BINTABLE'}

    return x

## ext slices for image section
def ext_slices_sect(s):
    '''
        extract slices for image section
    '''
    m=ptn_syn_sect.fullmatch(s)
    if not m:
        return None

    items=ptn_slice.findall(s)

    return [ext_slice_sectitem(*t) for t in items]

def ext_slice_sectitem(*args):
    '''
        extract slice from an item of section

        2 types of arguments:
            1 arg: string of slice
            4 args: groups from `ptn_slice`
    '''
    if len(args)==1:
        print(args)
        m=ptn_slice.fullmatch(args[0])
        assert m
        args=m.groups()
    elif len(args)!=4:
        raise Exception('only support 1 or 4 args, but got %i' % len(args))

    # groups from `ptn_slice`
    asterisk, start, end, step=args

    # step
    if not step:
        step=1
    else:
        step=int(step)

    # asterisk
    if asterisk:
        if asterisk[0]=='-':
            step*=-1
        return None, None, step

    # start, end
    start=int(start)
    end=int(end)

    return start, end, step
