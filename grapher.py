#!/usr/bin/env python
# plot and annotate lpcm wave files easily

# TODO;
# - consider moving sox coversion to be in this module so we can open
# arbitrarly formatted audio files into numpy arrays

from imp import reload
import numpy as np
import matplotlib.pyplot as plt
import wave
#from scipy.io import wavfile
# from scipy import signal
# from scipy import fftpack

import subprocess, os
import os.path as path

class SigPack(object):
    def __init__(self, wave_file_list):
        self.flist = []
        self._vectors = {}
        self.fig = None
        self.add(wave_file_list)

        # TODO: make scr_dim impl more pythonic
        self.w, self.h = scr_dim()

    def _loadsig(self, index):
        try:
            print("loading wave file : ",path.basename(self.flist[index]))

            # read audio data and params
            sig, self.fs, self.bd = wav_2_np(self.flist[index])
            # (self.fs, sig) = wavfile.read(self.flist[index])

            amax = 2**(self.bd - 1) - 1
            sig = sig/amax
            self._vectors[index] = sig
            print("INFO |->",len(sig),"samples =",len(sig)/self.fs,"seconds @ ",self.fs," Hz")
        except:
            raise Exception("E: Failed to open wave file for plotting!\nEnsure that the wave file exists and is in LPCM format!")

    @property
    def show(self):
        '''just a pretty printer for the internal path list'''
        #FIXME: throw an error if table is empty
        if self.flist:
            print_table(map(path.basename, self.flist))
        else:
            print("E: no file list exists yet!?...")

    def close_all_figs(self):
        plt.close('all')
        self.fig = None

    @property
    def free_cache(self):
        self._vectors.clear()

    def fullscreen(self):
        if self.mng:
            self.mng.full_screen_toggle()
        else:
            print("no figure handle exists?")

    def vector(self, index):
        # path exists and vector loaded
        if index in self._vectors.keys() and type(self._vectors[index]) == np.ndarray:
            # print("the file ", self.flist[index], "is already cached in _vectors dict!")
            return self._vectors[index]

        # path exists but vector not yet loaded
        elif self._vectors.get(index) == None:
            self._loadsig(index)
            return self._vectors[index]

        # request for an index which doesn't reference a path
        elif index not in self._vectors.keys():
            print("Error: you requested an index out of range!")
            raise ValueError("no file path exists for index : " + str(index) + " see SigPack.show")
        else:
            raise ValueError("weird stuffs happening heres!")

    def add(self, paths):
        '''Add a wave file path to the SigPack.\n
        Can take a single path or a sequence of paths as input'''
        indices = []
        paths = iter(paths) # always make paths an iterable

        # a sequence of paths? -> generate look-up indices
        for p in paths:
            if path.exists(p):
                if p not in self.flist:
                    self.flist.append(p)
                    self._vectors[self.flist.index(p)] = None
                else:
                    print(path.basename(p), "is already in our path list -> see grapher.SigPack.show")
            else:
                raise ValueError("path string not valid?!")

            yield self.flist.index(p)

    def prettify(self):
        # tighten up the margins
        self.fig.tight_layout(pad=1.03)

    def plot(self, *indices):
        axes = []
        wp_indices = [elem for elem in indices if type(elem) == int]

        if len(wp_indices) == 0:
            print("E: you must specify integer indices which correspond to paths in self.flist\n"
                  "see self.show for listing")
        else:
            return [axis for axis in self._plot(wp_indices)]
            # for axis in self._plot(wp_indices):
            #     axes.append(axis)

    # a lazy plotter to save aux space?
    def itr_plot(self, items):
        # if they're simple indices compile them now
        wp_indices = [elem for elem in items if type(elem) == int]

        if len(wp_indices) == 0:
        # (i.e. if not ints)
            for i in self.add(items):
                wp_indices.append(i)

        for axis in self._plot(wp_indices):
            yield axis

    # plot generator - uses 'makes sense' figure / axes settings
    def _plot(self, index_itr, start_time=0, samefig=True, title=None):
        axes = {}
        if type(index_itr) != 'list':
            indices = [i for i in index_itr]

        # create a new figure and format
        if not samefig or not self.fig:
            self.fig = plt.figure()
            self.mng = plt.get_current_fig_manager()
        else:
            self.fig.clf()

        # set window to half screen size if only one signal
        if len(indices) < 2:
            h = self.h/2
        else:
            h = self.h
        try:
            self.mng.resize(self.w, h)
        except:
            raise "unable to resize windows!?"
        # self.fig.set_size_inches(10,2)
        # self.fig.tight_layout()

        for icount, i in enumerate(indices):

            # t = np.arange(start_time, len(self.vector(i)) / self.fs, 1/self.fs)
            t = np.linspace(start_time, len(self.vector(i)) / self.fs, num=len(self.vector(i)))
            # print("size of t is ", len(t))

            ax = self.fig.add_subplot(len(indices), 1, icount + 1)
            ax.plot(t, self.vector(i), figure=self.fig)

            font_style = {'size' : 'small'}

            if title == None:
                ax.set_title(path.basename(self.flist[i]), fontdict=font_style)
            else:
                ax.set_title(title, fontdict=font_style)

            ax.set_xlabel('Time (s)', fontdict=font_style)
            yield ax

    @property
    def get_figure():
        return self.fig

    def find_wavs(self, sdir):
        self.flist = file_scan('.*\.wav$', sdir)
        for i, path in enumerate(self.flist):
            self._vectors[i] = None
        print("found", len(self.flist), "files")

def vline(axis, time, label='this is a line?', colour='r'):

    # use ylim for annotation placement
    mx = max(axis.get_ylim())

    # add a vertical line
    axis.axvline(x=time, color=colour)
    # add a label to the line
    axis.annotate(label,
                  xy=(time, mx),
                  xycoords='data',
                  xytext=(3, -10),
                  textcoords='offset points')
                  # arrowprops=dict(facecolor='black', shrink=0.05),
                  # horizontalalignment='right', verticalalignment='bottom')
    return axis

def line_max_y(axis):
    # use max value from the available lines for annotation placement
    lines = axis.get_lines()
    mx = 0
    for line in lines:
        lm = max(line.get_ydata())
        if lm > mx:
            mx = lm
    return mx

def print_table(itr, field_header=['wave files'], delim='|'):

    itr = list(itr)
    max_width = max(len(field) for field in itr)
    widths = iter(lambda:max_width, 1) # an infinite width generator

    # print a field title header
    print('')
    print('index', delim, '',  end='')
    for f, w in zip(field_header, widths):
        print('{field:<{width}}'.format(field=f, width=w), delim, '', end='')
    print('\n')

    # print rows
    for row_index, row in enumerate(itr):
        # print index
        print('{0:5}'.format(str(row_index)), delim, '', end='')
        print('{r:<{width}}'.format(r=row, width=max_width), delim, '', end='')
        print()
        # # print columns
        # for col, w in zip(row, widths):
        #     print('{column:<{width}}'.format(column=col, width=w), delim, '', end='')
        # print()

def file_scan(re_literal, search_dir, method='find'):
    if method == 'find':
        try:
            found = subprocess.check_output(["find", search_dir, "-regex", re_literal])
            paths = found.splitlines()

            # if the returned values are 'bytes' then convert to strings
            str_paths = [path.abspath(b.decode()) for b in paths]
            return str_paths

        except subprocess.CalledProcessError as e:
            print("scanning logs using 'find' failed with output: " + e.output)

    elif method == 'walk':
        #TODO: os.walk method
        print("this should normally do an os.walk")
    else:
        print("no other logs scanning method currentlyl exists!")

def wav_2_np(f):
    ''' use the wave module to make a np array'''
    wf = wave.open(f, 'r')
    fs = wf.getframerate()
    bd = wf.getsampwidth() * 8  # bit depth calc
    frames = wf.readframes(wf.getnframes())
    # hack to read data using array protocol type strings
    dt = np.dtype('i' + str(wf.getsampwidth()))
    sig = np.fromstring(frames, dtype=dt)
    wf.close()
    return (sig, fs, bd)

def scr_dim():
    #TODO: find a more elegant way of doing this...say using
    # figure.get_size_inches()
    # figure.get_dpi()
    dn = path.dirname(path.realpath(__file__))
    bres = subprocess.check_output([dn + "/screen_size.sh"])
    dims = bres.decode().strip('\n').split(sep='x')  # left associative
    return tuple([i for i in map(int, dims)])

def test():
    # example how to use the lazy plotter
    wp = SigPack([])
    wp.find_wavs('/home/tyler/code/python/wavs/')
    # wp.plot(0)
    return wp

if __name__ == '__main__':
    wp = test()
