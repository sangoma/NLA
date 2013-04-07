#!/usr/bin/env python
# plot and annotate lpcm wave files easily

# TODO;
# - f to plot single signal which can be easily called from cli
# - consider moving sox coversion to be in this module

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
# from scipy import signal
# from scipy import fftpack

import subprocess, os
from os.path import basename as basename

class WavPack(object):
    def __init__(self, wave_file_list):
        # self.row = 1
        # self.col = 1
        self._vectors = {}
        self.flist = wave_file_list
        self.fig = None

    def _loadwav(self, index):
        if index > len(self.flist):
            print("Error: you requested an index out of range!")
        elif type(self._vectors[index]) ==  'np.ndarray':
            print("Warning: the file ", self.flist[index], "is already cached in _vectors table!")
        else:
            try:
                print("-> loading wave file : ", basename(self.flist[index]))
                # should use the wave module instead?
                (self.fs, sig) = wavfile.read(self.flist[index])
                sig = sig/max(sig)
                self._vectors[index] = sig
            except:
                print("Failed to open wave file for plotting!\nEnsure that the wave file is in LPCM format!")

    @property
    def show(self):
        print_table(map(basename, self.flist))

    @property
    def close_all_figs(self):
        plt.close('all')

    @property
    def reset_cache(self):
        self._vectors.clear()

    def vector(self, i):
        # if self._vectors.__contains__(i):
        if self._vectors.get(i) == None:
            self._loadwav(i)
        return self._vectors[i]

    def add_wav(self, path):
        self.flist.append(path)
        self._vectors[self.flist.index(path)] = None

    def plt(self, *indices, start_time=0, samefig=True):

        axes = []
        # # clear the figure if it exists already
        # if samefig and self.fig:
        #     self.fig.clf()
        # elif not (samefig and self.fig):
        #     # create new figures on every call
        self.fig = plt.figure()

        # self.fig.tight_layout()

        for iplot, i in enumerate(indices):

            t = np.arange(start_time, len( self.vector(i) )/self.fs, 1/self.fs)
            # print(len(indices))
            # print(iplot)

            ax = self.fig.add_subplot(len(indices), 1, iplot + 1)
            ax.plot(t, self.vector(i))
            # ax.axis('tight')

            ax.set_title("wav " + str(i) + " : " + basename(self.flist[i]))
            ax.set_ylabel('Amplitude')
            ax.set_xlabel('Time (s)')
            # ax.show()
            axes.append(ax)

        return axes

    def vline_annotate(self, axes, time, label='a line?'):

        # add a vertical line
        axes.axvline(x=time, color='r')

        # add a label to the line
        xy = (time, 1)
        axes.annotate(label, xy)

    # @property
    # def figure():
    #     return self.fig
    def find_wavs(self, sdir):
        self.flist = file_scan('.*wav', sdir)
        for i, path in enumerate(self.flist):
            self._vectors[i] = None
        print("found", len(self.flist), "files")

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
            found = subprocess.check_output(["find", search_dir, "-regex", "^.*" + re_literal + ".*"])
            paths = found.splitlines()

            # TODO: move this up to line 64
            # if the returned values are 'bytes' then convert to strings
            str_paths = [b.decode() for b in paths]
            return str_paths

        except subprocess.CalledProcessError as e:
            print("scanning logs failed with output: " + e.output)

    elif method == 'walk':
        #TODO: os.walk method
        print("this should normally do an os.walk")
    else:
        print("no other logs scanning method currentlyl exists!")

# Main?
g = WavPack([])
