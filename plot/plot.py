#!/usr/bin/env python3

'''
    class used for plot of model fitting
'''

import os
import numbers

import re

import numpy as np

from astropy.io import fits
from astropy.visualization import AsinhStretch, ImageNormalize

from matplotlib.colors import Normalize

import datapy.plot as dplt

from .line import Line2D
from galfit.galfit import GalFit
import galfit.fits as gfits

class FitPlot:
    '''
        used to plot fitting result
    '''
    def __init__(self, obs, mod, mask=None, sigma=None, sky=None):
        '''
            init work

            load necessary (and some optional) images
        '''
        # obs and mod image
        self._obs=self.load_img(obs)
        self._mod=self.load_img(mod)

        if sky is not None:
            self._obs=self._obs-sky
            self._mod=self._mod-sky

        # residual
        self._re=self._obs-self._mod

        # mask
        if mask is not None:
            mask=self.load_mask(mask)
        self._mask=mask

        ## mask bad pixel in obs
        self.add_bad_obs_to_mask()

        # sigma
        if sigma is not None:
            sigma=self.load_img(sigma)
        self._sigma=sigma

        # lines to plot
        self._lines=[]

    # load fits
    def load_img(self, img):
        '''
            load image

            :param img: str or ndarray
        '''
        if isinstance(img, str):
            return self.load_fits(img)
        return img

    @staticmethod
    def load_fits(fname):
        '''
            load FITS file
        '''
        return gfits.getdata(fname)

    ## mask file
    def load_mask(self, mask):
        '''
            get bool array for mask
                True for good pixel

            :param mask: str, ndarray
                if str, FITS file
                    positive value for bad pixels
        '''
        if isinstance(mask, str):
            mask=self.load_fits(mask)
        else:
            mask=np.asarray(mask)

        if mask.dtype!='bool':
            mask=mask<=0

        return mask

    def add_bad_obs_to_mask(self):
        '''
            mask invalid pixel in observed
        '''
        if self._mask is None:
            return

        mask=np.logical_not(np.isfinite(self._obs))
        self._mask[mask]=0

    # interpolation line
    def add_line(self, x0, y0, angle, lrange=None, deg=True):
        '''
            add line for given center (x0, y0) and angle
                where angle is from x-axis

            :param lrange: optional
                optional length range for sampler
        '''
        line=Line2D(x0, y0, angle, deg=deg, lrange=lrange)
        self._lines.append(line)

        return line

    ## frequently used methods
    def add_line_center(self, angle, **kwargs):
        '''
            add line through center of image
        '''
        ny, nx=self._obs.shape

        return self.add_line(nx/2, ny/2, angle, **kwargs)

    # figure, axes
    def create_figaxes(self, cbar=True, rcb=0.03, rline=0.2,
                             minsep=2, minmarg=20, minaxw=200,
                             nchar_ytick=3):
        '''
            create figure and axes

            Parameters:
                cbar: bool
                    whether plot cbar

                rcb: float
                    height ratio between
                        color bar axes and image axes

                rline: float
                    height ratio between
                        line plot axes

                minsep: float
                    min separation between model axes and residual axes
                        in unit of 'points'

                minmarg: float
                    min margins, in unit 'points'

                minaxw: float
                    min width of image axes, in unit 'points'

                nchar_yticl: int
                    number of char for y-tick
        '''
        self._cbar=cbar
        nline=len(self._lines)

        # layout
        manager=dplt.init()
        root=manager.rect

        grid=manager.add_grid(ny=1, nx=bool(nline)+1)
        grid0=grid[0, 0].add_grid(nx=3, ny=1+int(cbar))
        if nline:
            grid1=grid[0, 1].add_grid(nx=nline, ny=2)

        # subgrid binded to parent
        grid0.set_margins_zero()
        if nline:
            grid1.set_margins_zero()

        # rects to place axes
        rects_img=[grid0[-1, i] for i in range(3)]
        if cbar:
            rects_cb=[grid0[0, :2], grid0[0, 2]]
        else:
            rects_cb=[]

        if nline:
            rects_line=grid1.get_rects('col', reverse=True)
        else:
            rects_line=[]

        # size along x-axis
        ## width
        grid0.set_dists_equal('width')
        if nline:
            grid1.set_dists_equal('width')
            grid0.w0=grid1.w0

        ## wspaces
        wsp00=grid0.wspaces[0]
        wsp01=grid0.wspaces[1]
        wsp00.set_to(0)

        if nline>1:
            grid1.set_dists_val(wsp00, 'wspace')

        # y-axis
        ## height ratio between axes
        if cbar:
            rect0, rect1=rects_img[0], rects_cb[0]
            rect1.height=rcb*rect0.height

        if nline:
            rect0, rect1=rects_line[0]
            rect1.height=rline*rect0.height

        ## hspaces
        if cbar and nline:
            grid1.hspaces[0].set_to(grid0.hspaces[0])

        # equal aspect ratio
        rects_img[0].set_aspect_equal()

        # minsize
        pts=manager.get_points_size()

        ## separation between model axes and residual
        msp=minsep*pts
        wsp01.set_ge(msp)
        if cbar:
            grid0.hspaces[0].set_ge(msp)
        if nline:
            grid1.hspaces[0].set_ge(msp)

        ## margins
        manager.set_dists_ge(minmarg*pts, *grid.margins)

        ## width of axes
        rects_img[0].width.set_ge(minaxw*pts)

        ## wspace to place x/y-ticks
        minxtick=manager.get_sepsize_tick('x', out=False, nchar=2)
        grid.hmargins[0].set_ge(minxtick)

        minytick=manager.get_sepsize_tick('y', out=False, nchar=nchar_ytick)
        grid.wmargins[0].set_ge(minytick)
        if nline:
            grid.wspaces[0].set_ge(minytick)

        ## tight layout
        manager.set_width_to_min()
        manager.set_height_to_min()
        if nline:
            manager.set_to_max(rects_line[0][0].height)

        # create axes
        sharex=[rects_img]
        sharey=[rects_img]
        if nline:
            sharex.append([])
            for rects in rects_line:
                sharex[-1].extend(rects)

            sharey.extend(zip(*rects_line))

        fig, (axes_imgs, axes_line, axes_cbar)=\
                manager.create_axes_in_rects(
                            [rects_img, rects_line, rects_cb],
                            style='tight grid',
                            sharex=sharex, sharey=sharey)

        # axis off
        for ax in axes_imgs:
            ax.axis('off')

        self._fig=fig
        self._axes_imgs=axes_imgs
        self._axes_line=axes_line
        self._axes_cbar=axes_cbar

    # imshow
    @staticmethod
    def get_imag_norm(vmin, vmax, norm='linear'):
        '''
            get norm for imshow of an image

        Parameters:
            vminmax: (vmin, vmax)
                range to show

            norm: 'linear' or 'log', or `Normalize` instance
                'log': a log-like norm
                    often used for galaxy image
                    use `AsinhStretch` actually,
                        asinh(x) ~ x, for small x
                                 ~ log(x), for large x

                'linear': linear norm
                    often used for residual image

        '''
        if isinstance(norm, Normalize):
            return norm

        if norm=='log':
            norm=ImageNormalize(vmin=vmin, vmax=vmax, stretch=AsinhStretch())
        elif norm=='linear':
            norm=ImageNormalize(vmin=vmin, vmax=vmax)
        else:
            raise ValueError('unexpected norm: %s' % norm)

        return norm

    @staticmethod
    def get_vminmax(data, vmm=None, vq=None):
        '''
            get range of value in `imshow`

            Parameters:
                vmm: (vmin, vmax)

                vq: float, or quantiles for (vmin, vmax)
                    vminmax quantile

                    if float, q0, q1=1-vq, vq or vq, 1-vq
                    if tuple, q0, q1=vq
                    if None, vq=0.9 by default
                    
                    combine `vmm` and `vq` to determine (vmin, vmax)
                        allow None for non-determined
        '''
        vmin=vmax=None

        if vmm is not None:
            vmin, vmax=vmm

        if vq is not None:
            if isinstance(vq, numbers.Number):
                q0=min(vq, 1-vq)
                q1=1-q0
            else:
                q0, q1=vq

            data=np.asarray(data)

            # mask non-finite data
            data=data[np.isfinite(data)]

            if q0 is not None:
                assert vmin is None, 'conflict for `vmin`'
                vmin=np.quantile(data, q0)

            if q1 is not None:
                assert vmax is None, 'conflict for `vmax`'
                vmax=np.quantile(data, q1)

        assert vmin<vmax

        return vmin, vmax

    def set_obsmod_norm(self, vminmax=(0, None), vq=(None, 0.9),
                              data='mod', norm='log'):
        '''
            set norm for imshow of `obs` and `mod` image
            default setup is coded
        '''
        # image data
        if data=='mod':
            data=self._mod
        elif data=='obs':
            data=self._obs
        else:
            raise ValueError('unexpected image data: %s' % data)

        vmin, vmax=self.get_vminmax(data, vmm=vminmax, vq=vq)
        self._norm_om=self.get_imag_norm(vmin, vmax, norm=norm)

    def set_residu_norm(self, vminmax=None, vq=0.9,
                              norm='linear', symmetry=True):
        '''
            set norm for imshow of residual image
            default setup is coded
        '''
        data=self._re
        if self._mask is not None:
            data=data[self._mask]

        vmin, vmax=self.get_vminmax(data, vmm=vminmax, vq=vq)

        if symmetry:
            assert vmax>0

            vmax=max(vmax, -vmin)
            vmin=-vmax

        self._norm_re=self.get_imag_norm(vmin, vmax, norm=norm)

    def imshow_imgs(self, cmap=None, extent='base0',
                          aspect='equal', origin='lower', **kwargs):
        '''
            show 3 images in order:
                obs, mod, re

            Parameters:
                extent: None, string, or scalars (left, right, bottom, up)
                                                 (left, bottom)
                    if only two arguments,
                        use left+nx, bottom+ny for right and up

                    if None, use `matplotlib` default

                    if string, only 'base0' or 'base1'
                        if 'base0', use (-0.5, -0.5)
                        if 'base1', use (0.5, 0.5)

                cmap, kwargs: same as `plt.imshow`
        '''
        # data
        obs, mod, re=self._obs, self._mod, self._re

        ny, nx=obs.shape

        # extent
        if isinstance(extent, str):
            if extent=='base0':
                extent=(-0.5, -0.5)
            elif extent=='base1':
                extent=(0.5, 0.5)
            else:
                raise Exception('unexpected extent: %s' % extent)

        if extent is not None:
            if len(extent)==2:
                x0, y0=extent
                extent=(x0, x0+nx, y0, y0+ny)
            else:
                assert len(extent)==4

        # norm
        if not hasattr(self, '_norm_om'):
            self.set_obsmod_norm()
        norm_om=self._norm_om

        if not hasattr(self, '_norm_re'):
            self.set_residu_norm()
        norm_re=self._norm_re

        # axes
        if not hasattr(self, '_fig'):
                self.create_figaxes()

        fig=self._fig
        axobs, axmod, axre=self._axes_imgs

        # imshow
        kwargs.update(cmap=cmap, extent=extent, aspect=aspect,
                      origin=origin)

        imobs=axobs.imshow(obs, norm=norm_om, **kwargs)
        axmod.imshow(mod, norm=norm_om, **kwargs)
        
        imre=axre.imshow(re, norm=norm_re, **kwargs)

        ## set lim
        x0, x1, y0, y1=imobs.get_extent()

        axobs.set_xlim([x0, x1])
        axobs.set_ylim([y0, y1])

        ## color bar
        if self._axes_cbar:
            axcbom, axcbre=self._axes_cbar

            fig.colorbar(imobs, cax=axcbom, orientation='horizontal') 
            fig.colorbar(imre, cax=axcbre, orientation='horizontal')

    # plot comparison along lines
    ## set samplers
    def get_lrange_in_image(self, line, margin=0):
        '''
            get range in image with shape (ny, nx)
        '''
        ny, nx=self._obs.shape

        x0, x1=margin, nx-1-margin
        y0, y1=margin, ny-1-margin

        return line.get_length_range_in_rect(x0, x1, y0, y1)

    def get_sampler(self, line, arg=None, lrange=None, margin=5,
                          how='num', imgcut=True):
        '''
            return a sampler of a line

            Parameters:
                lrange: range of length to sample
                    if None, use default range (if set)
                                 or ranges in image

                arg: `num` or `step` to determine sampler
                    if None, use default setup
                        num=50 or step=1

                how: 'num' or 'step'
                    way to get sampling points

                imgcut: bool
                    whether cut line in image region
        '''
        if lrange is None:
            if line.has_lrange():
                l0, l1=line.get_lrange()
            else:
                l0, l1=self.get_lrange_in_image(line, margin)
        elif isinstance(lrange, numbers.Number):
            l0, l1=-lrange, lrange
        else:
            l0, l1=lrange

        # cut in image region
        if imgcut:
            lm0, lm1=self.get_lrange_in_image(line, margin)

            l0=max(l0, lm0)
            l1=min(l1, lm1)

        # way to get points
        if how=='num':
            f=line.sampler_num
            if arg is None:
                arg=50
        elif how=='step':
            f=line.sampler_step
            if arg is None:
                arg=1
        else:
            raise ValueError('unexpected sampler method')

        return f(l0, l1, arg)

    def set_sampler_obs(self, arg=None, lrange=None, how='step', **kwargs):
        '''
            sampler in obs and residual images
        '''
        kwargs.update(arg=arg, lrange=lrange, how=how)
        self._sampler_obs=[]
        for line in self._lines:
            sampler=self.get_sampler(line, **kwargs)
            self._sampler_obs.append(sampler)

    def set_sampler_mod(self, arg=1000, lrange=None, how='num', **kwargs):
        '''
            sampler in model images
        '''
        kwargs.update(arg=arg, lrange=lrange, how=how)
        self._sampler_mod=[]
        for line in self._lines:
            sampler=self.get_sampler(line, **kwargs)
            self._sampler_mod.append(sampler)

    ## sample in obs image
    def plot_sampler_obs(self, axs, sampler, show_mask_points=True,
                            s=2, marker='o', elinewidth=1, 
                            kws_mplot={}, **kwargs):
        '''
            plot a line sampler in obs and residual 

            :param show_mask_points: bool, default
                whether to show mask points

                `kws_mplot`: keyword arguments for mask points plot
        '''
        axobs, axre=axs

        xs=sampler.lengths

        ysobs=sampler(self._obs)
        ysre=sampler(self._re)

        # sigma
        yerr=None
        if self._sigma is not None:
            yerr=sampler(self._sigma)

        # mask
        ysobs_mask=None
        if self._mask is not None:
            mask=sampler(self._mask)

            if show_mask_points:
                m=np.logical_not(mask)

                xs_mask=xs[m]
                ysobs_mask=ysobs[m]
                ysre_mask=ysre[m]
                yerr_mask=yerr[m] if yerr is not None else None

            xs=xs[mask]
            ysobs=ysobs[mask]
            ysre=ysre[mask]
            yerr=yerr[mask] if yerr is not None else None

        # plot
        kws1=dict(marker=marker, markersize=s, elinewidth=elinewidth)

        axobs.errorbar(xs, ysobs, yerr=yerr, ls='', **kws1, **kwargs)
        axre.errorbar(xs, ysre, yerr=yerr, ls='', **kws1, **kwargs)

        if ysobs_mask is not None:
            for k, v in kws1.items():
                if k not in kws_mplot:
                    kws_mplot[k]=v
            axobs.errorbar(xs_mask, ysobs_mask, yerr=yerr_mask, ls='', **kws_mplot)
            # axre.errorbar(xs_mask, ysre_mask, yerr=yerr_mask, ls='', **kws_mplot)

    def plot_samplers_obs(self, **kwargs):
        '''
            plot all samplers in obs
        '''
        # check nessary attrs
        if not hasattr(self, '_fig'):
            self.create_figaxes()

        if not hasattr(self, '_sampler_obs'):
            self.set_sampler_obs()

        # plot
        for axs, sampler in zip(self._axes_line, self._sampler_obs):
            self.plot_sampler_obs(axs, sampler, **kwargs)

    ## sample in mod image
    def plot_sampler_mod(self, axs, sampler, ls='-', axhls='--',
                                lw=1.2, axhlw=1,
                                color='black', axhlc='black', **kwargs):
        '''
            plot a line sampler in mod image

            TO SUPPORT:
                sample in subcomponent images
        '''
        axmod, axre=axs

        xs=sampler.lengths
        ys=sampler(self._mod)

        axmod.plot(xs, ys, ls=ls, lw=lw, color=color, **kwargs)
        axre.axhline(0, ls=axhls, lw=axhlw, color=axhlc)

    def plot_samplers_mod(self, **kwargs):
        '''
            plot all samplers in mod
        '''
        # check nessary attrs
        if not hasattr(self, '_fig'):
            self.create_figaxes()

        if not hasattr(self, '_sampler_mod'):
            self.set_sampler_mod()

        # plot
        for axs, sampler in zip(self._axes_line, self._sampler_mod):
            self.plot_sampler_mod(axs, sampler, **kwargs)

    ## add interpolation curve to images
    def plot_line_sampler_in_image(self, sampler, color='white', **kwargs):
        '''
            plot line sampler in image axes
        '''
        ys, xs=sampler.coords

        i0, i1=np.argmin(xs), np.argmax(xs)
        x0, y0=xs[i0], ys[i0]
        x1, y1=xs[i1], ys[i1]

        # extent of image
        im=self._axes_imgs[0].get_images()[-1]
        extent=im.get_extent()
        ex=min(extent[:2])
        ey=min(extent[2:])

        dx, dy=ex+0.5, ey+0.5  # center of starting pixel

        # plot
        kwargs.update(color=color)
        for ax in self._axes_imgs:
            ax.plot((x0+dx, x1+dx), (y0+dy, y1+dy), **kwargs)

    def plot_samplers_in_image(self, **kwargs):
        '''
            plot all samplers in image axes
        '''
        # check nessary attrs
        if not hasattr(self, '_fig'):
            self.create_figaxes()

        if not hasattr(self, '_sampler_obs'):
            self.set_sampler_obs()

        # plot
        for sampler in self._sampler_obs:
            self.plot_line_sampler_in_image(sampler, **kwargs)

    ## decorate of line plot axes
    ### yscale
    def set_yscale_lines(self, yscale):
        '''
            yscale of line plot axes
        '''
        # only set one, already sharey
        for axs in self._axes_line[:1]:
            ax=axs[0]
            ax.set_yscale(yscale)

    def set_ylog_lines(self):
        '''
            set log yscale of lines axes
        '''
        self.set_yscale_lines('log')

    ### ylim
    def set_ylim_lines_obs(self, ylim):
        '''
            set ylim of line plot in obs
        '''
        for axs in self._axes_line[:1]:
            ax=axs[0]
            ax.set_ylim(ylim)

    def set_ylim_lines_re(self, ylim):
        '''
            set ylim of line plot in re

            :param ylim: 2-tuple, float, or 'sym'
                ylim for plot of re line

                2-tuple: (y0, y1)

                single float y: (-y, y)

                'sym': means symmetrical ylim
        '''
        if ylim=='sym':
            self.set_ylim_sym_lines_re()
            return

        if isinstance(ylim, numbers.Number):
            ylim=[-ylim, ylim]

        for axs in self._axes_line[:1]:
            ax=axs[1]
            ax.set_ylim(ylim)

    def set_ylim_lines(self, ylobs, ylre):
        '''
            set ylim of both line plots
        '''
        self.set_ylim_lines_obs(ylobs)
        self.set_ylim_lines_re(ylre)

    def set_ylim_sym_lines_re(self):
        '''
            set ylim symmetrical for plot of re line
        '''
        for axs in self._axes_line[:1]:
            ax=axs[1]

            y0, y1=ax.get_ylim()
            ym=max(abs(y0), abs(y1))

            ax.set_ylim([-ym, ym])

    ### pack of all samplers plotting
    def plot_lines(self, ylog=True, ylim_re='sym', ylim_obs=None,
                        show_mask_points=True, kws_mplot={},
                        kws_obs={}, kws_mod={}, kws_line={}):
        '''
            plot lines for interpolations along lines

            :param ylim_re: 2-tuple, float, or 'sym'
                ylim for plot of re line

                2-tuple: (y0, y1)

                single float y: (-y, y)

                'sym': means symmetrical ylim

            :param show_mask_points: bool
                whether to show mask points in obs image

                `kws_mplot` to specify distinguished style with non-masked points
        '''
        # obs and re
        self.plot_samplers_obs(show_mask_points=show_mask_points, 
            kws_mplot=kws_mplot, **kws_obs)

        # mod
        self.plot_samplers_mod(**kws_mod)

        # add sampler curve in image
        self.plot_samplers_in_image(**kws_line)

        # decorate
        if ylog:
            self.set_ylog_lines()

        if ylim_obs is not None:
            self.set_ylim_lines_obs(ylim_obs)

        if ylim_re is not None:
            self.set_ylim_lines_re(ylim_re)

    # save to file or show in GUI
    def show(self):
        '''
            show in GUI
        '''
        dplt.show()

    def savefig(self, fname, *args, **kwargs):
        '''
            save to a file
        '''
        self._fig.savefig(fname, *args, **kwargs)

    # properties
    @property
    def fig(self):
        '''
            figure
        '''
        return self._fig

    @property
    def axes_image(self):
        '''
            return 1st image axes
        '''
        return self._axes_imgs[0]

    @property
    def axes_line(self):
        '''
            return 1st axes pair for line plot
                including 2 axes
                    (obs, re)
        '''
        return self._axes_line[0]

# combine with galfit file
class GFPlot(FitPlot):
    '''
        combine with galfit file
    '''
    def __init__(self, fname, mask=True, sigma=True, sky=True,
                       run_gf=None, verbose_gf=False):
        '''
            init

            load image data from img block related in galfit file

            :param run_gf: None, bool
                whether to run galfit before init

                if None, output file would be checked
                    if the output not match with gf file, run gf again

                if True, run with imgblock model
        '''
        gf=GalFit(fname)

        # imgblock
        fblk=gf.get_path_of_file_par('output')

        # check output file
        blkhdus=fits.open(fblk)
        if run_gf is None:
            if len(blkhdus)!=4:
                run_gf=True
            else:
                dname=os.path.dirname(fblk)
                hdr=blkhdus[2].header
                gfile_blk=os.path.join(dname, hdr['LOGFILE'])
                if not os.path.isfile(gfile_blk):  # happens when only create model image
                    gfile_blk=os.path.join(dname, hdr['INITFILE'])

                if not os.path.samefile(gfile_blk, gf.srcfname):
                    run_gf=True
                else:
                    run_gf=False

        # run gf
        if run_gf:
            self._run_gf_imgblock(fname, verbose=verbose_gf)

        # region
        if mask or sigma:
            x1, x2, y1, y2=gf.region
            sreg=f'[{x1}:{x2},{y1}:{y2}]'

        # mask
        kwargs={}

        if mask:
            mask=gf.get_path_of_file_par('mask')
            if mask is None:
                print('warning: mask par not set')
            kwargs['mask']=mask+sreg

        # sigma
        if sigma:
            sigma=gf.get_path_of_file_par('sigma')
            if sigma is None:
                print('warning: sigma par not set')
            kwargs['sigma']=sigma+sreg

        # sky
        if sky:
            sky=0
            for mod in gf:
                if not mod.is_sky():
                    continue

                if mod.skip:  # Z=1
                    continue

                if mod.dbdx!=0 or mod.dbdy!=0:
                    raise Exception('only support flat sky')

                sky+=mod.bkg
            kwargs['sky']=sky

        # init FitPlot
        super().__init__(blkhdus[1].data, blkhdus[2].data, **kwargs)

        self._gf=gf

    def _run_gf_imgblock(self, fname, verbose=False):
        '''
            run galfit to create imgblock
        '''
        if not os.path.isfile(fname):
            raise FileNotFoundError('no gf file: %s' % fname)

        cmd='set -e; '

        dirname, gfname=os.path.split(fname)
        if dirname:
            cmd+='cd "%s"; ' % dirname

        cmd+='galfit -o2 "%s"' % gfname
        if not verbose:
            cmd+=' > /dev/null'

        errno=os.system(cmd)
        if errno!=0:
            raise RuntimeError('galfit failed for file: %s' % fname)

    # add line from model
    def add_line_thru_mod_center(self, i, angle, r, angle_to_pa=False):
        '''
            add line through center of a model

            :param r: float or 2-tuple of float
                range to plot

            :param angle_to_pa: bool
                whethen the arg `angle` is given relative to position angle
                if False, relative to x-axis
        '''
        mod=self._gf.comps[i]

        x0, y0=self._gf.region[::2]  # fit region
        xc, yc=mod.x0.val-x0, mod.y0.val-y0

        # angle
        if angle_to_pa:
            angle+=mod['pa']+90

        # range of line
        if isinstance(r, numbers.Number):
            assert r>0
            lrange=(-r, r)
        else:
            assert len(r)==2
            lrange=r

        self.add_line(xc, yc, angle, lrange=lrange)

    def add_line_mod(self, i, which='both', par='pa',
                            rpar='auto', rscale=2,
                            ba='auto'):
        '''
            add line in model

            Parameters:
                i: int
                    index of model in galfit

                which: 'both', 'major', 'minor'
                    which line to add

                par: str
                    parameter of position angle

                    NOTE: pa is angle between major axis of model and y-axis

                rpar: str or None
                    par for scale radius

                    if 'auto', use 're' or 'rs' (actually 1.678*rs)
                    if None, use all segments in image

                rscale: float
                    how many times of re to plot

                ba: float or 'auto'
                    b/a ratio, used to determine lrange along minor
                    acts only when plot minor

                    if 'auto', use 'ba' or 'hs/2rs', or 1 by default
        '''
        mod=self._gf.comps[i]

        x0, y0=self._gf.region[::2]  # fit region

        xc, yc=mod.x0.val-x0, mod.y0.val-y0
        angle=mod[par]+90  # +90 to angle with x-axis

        if isinstance(rpar, str):
            if rpar=='auto':
                if 're' in mod:
                    rpar='re'
                else:
                    assert 'rs' in mod
                    rpar='rs'

                re=float(mod[rpar])
                if rpar=='rs':
                    re*=1.678  # convert to re

        # which line
        major=minor=False
        if which=='both':
            major=minor=True
        elif which=='major':
            major=True
        elif which=='minor':
            minor=True
        else:
            raise ValueError('unexpected `which`: %s' % which)

        # add line
        r=re*rscale
        if major:
            self.add_line(xc, yc, angle, lrange=(-r, r))

        if minor:
            # ba
            if ba=='auto':
                if 'ba' in mod:
                    ba=mod['ba'].val
                elif 'hs' in mod and 'rs' in mod:
                    ba=(mod['hs']/2)/mod['rs']
                else:
                    ba=1

            r=r*ba
            self.add_line(xc, yc, angle+90, lrange=(-r, r))
