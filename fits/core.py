#!/usr/bin/env python3

'''
    core functions for io of fits
    
    use result of parser of extened file name,
        implemented in module `fitsname`
'''

import numpy as np

from ..dtype import is_int_type

# bottom function to locate HDU
def locate_hdu(hdulist, ext=None):
    '''
        locate a hdu in given hdulist

        Parameter:
            ext: None, int, or tuple
                if None, return first HDU
                if int, it is index of target HDU in list
                if tuple, two types:
                    1 element : same as int
                    3 elements: extname, extver, xtension
                        last two terms are optional,
                            None for missing

                        extname:  value of EXTNAME or HDUNAME keyword
                        extver:   value of EXTVER keyword
                        xtension: value of XTENSION keyword
    '''
    if ext is None:
        return hdulist[0]

    # extno
    if is_int_type(ext):
        return hdulist[ext]

    if len(ext)==1:
        k=ext[0]
        assert is_int_type(k)
        return hdulist[k]
    elif len(ext)!=3:
        raise ValueError('only support 1 or 4 elements in ext. '
                         'but got %i' % len(ext))

    # extname, extver, xtension
    extname, extver, xtension=ext
    assert extname is not None

    for hdu in hdulist:
        hdr=hdu.header

        # extname
        if 'EXTNAME' in hdr:
            if hdr['EXTNAME']!=extname:
                continue
        elif 'HDUNAME' in hdr:
            if hdr['HDUNAME']!=extname:
                continue
        else:
            continue

        # extver
        if extver is not None:
            if 'EXTVER' not in hdr:
                continue

            if hdr['EXTVER']!=extver:
                continue

        # xtension
        if xtension is not None:
            if 'XTENSION' not in hdr:
                continue

            xtension=normal_xtension(xtension)
            x0=normal_xtension(hdr['XTENSION'])
            if x0!=xtension:
                continue

        # find matched HDU
        return hdu

    # no HDU found
    s='EXTNAME='+extname  # error message
    if extver is not None:
        s+=', EXTVER=%i' % extver
    if xtension is not None:
        s+=', XTENSION=%s' % xtension

    raise ValueError('no HDU found for [%s]' % s)

# bottom function for image section
def image_section(hdu, sect=None):
    '''
        do image section to a HDU
            section is also done to WCS if existed

        Parameter:
            sect: None, or list of tuple (start, end, stop)
                if None, return a copy

                order of tuple in sect is same as 'NAXIS' in header

                sect would be normalize by `normal_sectlist`
                    if length of list is not equal to NAXIS
                        missing tuples are raised by (None, None, 1)

    '''
    assert hdu.is_image   # only do to image hdu

    hdu=hdu.copy()   # not change inplace

    if sect is None:
        return hdu

    # crop header at first
    #     if assign data to hdu.data, header also changes
    hdu.header=imgsect_crop_header(hdu.header, sect)

    # crop data
    hdu.data=imgsect_crop_data(hdu.data, sect)

    return hdu

## normalize image section tuple according to length in an axis
def normal_sectlist(sectlist, naxis):
    '''
        normal list of sect tuple acoording to naxis

        `naxis`: number of pixels in all axes
            order of tuple in list is same as 'NAXIS' in header

            if length of list is not equal to NAXIS
                missing tuples are raised by (None, None, 1)

    '''
    nax=len(naxis)

    # complete :param `sectlist` to the same as dims
    assert len(sectlist)<=nax
    if len(sectlist)<nax:
        sectlist.extend([(None, None, 1)*(nax-len(sectlist))])

    # normal sect tuple (start, end, step)
    return [normal_sect_item(s, nx) for s, nx in zip(sectlist, naxis)]

def normal_sect_item(item, nx):
    '''
        normalize a section tuple `(start, end, step)`
            according to axis length, `nx`

        support None or negative for start and end
            if negtive, meaning pixel couting from tail

            if None, meaning start or end in head or tail
                according to sign of step

        Result:
            start, end, step: all integral
                start, end: index starting from head
                    but 1 for head
                    might be 0 or negtive, meaning left of head

        Parameter:
            item: int, or tuple (start, end, step) or (start, end) or (end,)
                for int:
                    it means first or last some pixels
                        if positive or negative

                for tuple:
                    start, end, step: None, or non-zero integral

                    None for missing element

                    if step is None, use 1

            nx: number of pixel in the axis
    '''
    if is_int_type(item):
        end=item
        start=None

        step=1
        if end<0:
            step=-1
        elif end==0:   # no pixel included
            start=1
            end=0
    else:
        if len(item)==1:
            item=(None, *item, None)
        elif len(item)==2:
            item=(*item, None)
        elif len(item)!=3:
            raise Exception('only support int or tuples with 1,2,3 args')

        start, end, step=item

    # step
    if step is None:
        step=1
    assert step!=0

    # start, end
    start=norm_ind_pix(start, -step, nx)
    end=norm_ind_pix(end, step, nx)

    return start, end, step

def norm_ind_pix(ind, d, nx):
    '''
        normal index of pixel

        support nx=0 and ind=negative, None

        `nx`: number of pixel in the axis

        `ind` could be None, non-zero integral
            if None, sign of d (kind of direction) means to use head or tail 
                d<0 for head, and d>0 for end (only non-zero)

            if positive, 1 for the first pixel
            if negative, means index counting from end (-1 for the last)

        return index of pixel starting from head
            but 1 for head
                0 or negative for left of head
    '''
    assert nx>=0
    assert d!=0

    if ind is None:
        if d<0:
            return 1
        else:
            return nx

    # if not None, cannot be 0
    if ind<0:
        ind+=nx+1

    return ind

## function to image data
def imgsect_crop_data(data, sect=None):
    '''
        crop image data for given section `sect`

        Parameter:
            sect: list of tuple (start, end, step)
                `start` and `end` start from 1, not 0 as ndarray index

                order of tuple in list are x, y, ...
                    reversed with ndarray index
    '''
    if sect is None:
        return np.copy(data)

    naxis=list(reversed(data.shape))  # order of axis in fits header

    # normalize sect
    slices=[]
    for (x0, x1, d), nx in zip(normal_sectlist(sect, naxis), naxis):
        # assert nx>=0
        # assert d!=0

        if nx==0 or (x1-x0)*d<0:  # support empty axis
            slices.append(slice(2, 1))
            continue

        assert 1<=x0<=nx and 1<=x1<=nx

        # shift from pixel index to ndarray index
        x0-=1
        x1-=1

        # include end
        x1+=np.sign(d)
        if x1<0:
            x1=None

        slices.append(slice(x0, x1, d))

    return data[tuple(reversed(slices))]

## function to image header
def imgsect_crop_header(header, sect=None):
    '''
        crop FITS header for image section

        mainly handle WCS if existed

        work depends on keywords:
            CRPIX1, CRPIX2, ...
            CD1_1, CD1_2, CD2_1, CD2_2, ...
    '''
    header=header.copy() # not change in place

    if sect is None or 'CRPIX1' not in header:
        return header

    nax=header['NAXIS']
    naxis=[header['NAXIS%i' % i] for i in range(1, nax+1)]

    for i, (x0, _, d) in enumerate(normal_sectlist(sect, naxis)):
        assert d!=0

        # CRPIX
        key='CRPIX%i' % (i+1)
        header[key]=(header[key]-x0)/d+1  # +1 for 1-based pix index

        # CDj_i
        if d==1:
            continue

        for j in range(nax):
            key='CD%i_%i' % (j+1, i+1)
            header[key]*=d

    return header
