#!/usr/bin/env python
# plot and annotate lpcm wave files easily

# TODO;
# - f to plot single signal which can be easily called from cli
# - consider moving sox coversion to be in this module
# -

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
# from scipy import signal
# from scipy import fftpack

class WavSignal(object):
    def __init__(self, wave_file_path):
        self.row = 1
        self.col = 1
        self.vectors = []
        self.sig = np.array([])
        self.filepath = wave_file_path
        self.openwav(wave_file_path)

    def openwav(self, wave_file):
        try:
            (self.fs, sig) = wavfile.read(wave_file)
            sig = sig/max(sig)
            # self.vectors.append(sig)
            self.sig = sig

        except:
            print("Failed to open wave file for plotting!\n"
                  "Ensure that the audio file is in LPCM wave format!")
        # self.filepaths.append(wave_file)

    def plot(self, start_time=0):

        # create new figures on every call
        self.fig = plt.figure()
        t = np.arange(start_time, len(self.sig)/self.fs, 1/self.fs)

        # 1 row, 1 column, only plot
        ax = self.fig.add_subplot(1,1,1)
        ax.plot(t, self.sig)
        ax.axis('tight')
        # ax.set_title(self.filepath)
        ax.set_ylabel('Amplitude')
        ax.set_xlabel('Time (s)')

        return ax
        # ax.show()

    def vline_annotate(self, axes, time, label='a line?'):

        # add a vertical line
        axes.axvline(x=time, color='r')

        # add a label to the line
        xy = (time, 1)
        axes.annotate(label, xy)


# TODO: wavs bulk plotter?
class WavsPlotter(object):
    def __init__(self, wav_sig_obj):
        self.row = 1
        self.col = 1
        self.vectors = []
        pass
