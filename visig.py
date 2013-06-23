#!/usr/bin/env python
# plot and annotate lpcm wave files easily

# TODO;
# - consider moving sox coversion to be in this module so we can open
# arbitrarly formatted audio files into numpy arrays

from imp import reload
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import wave
#from scipy.io import wavfile
# from scipy import signal
# from scipy import fftpack
import subprocess, os
import gc
from collections import OrderedDict

# like it sounds : an ordered, int subscriptable dict
class OrderedIndexedDict(OrderedDict):

    def __getitem__(self, key):

        #TODO: how to handle this? (it's weird since we always have to check first)
        if isinstance(key, slice ):
            print("you've passed a slice! with start",key.start,"and stop",key.stop)
            return list(self.values())[key]
            # return OrderedIndexedDict(self.values())[key]

        # if it's already mapped get the value
        elif key in self:
            return OrderedDict.__getitem__(self, key)

        # TODO: is this the fastest way to implement this?
        # if it's an int iterate the linked list and return the value
        elif isinstance(key, int):
            return self[self._get_key(key)]
            # return self._setget_value(key)

    def __setitem__(self, key, value):
        # don't give me ints bitch...(unless you're chaning a value)
        # FIXME: this should reasign to the value @ int-key
        if isinstance(key, int):# raise KeyError("key can not be of type integer")
            # value = self._getset_value(key, new_value=value)
            key = self._get_key(key)

        OrderedDict.__setitem__(self, key, value)

        # set
        # if new_value:
        #     self[curr.key] = new_value
        #     return
        # # or get
        # else:
        #     return self[curr.key]
        # else: OrderedDict.__setitem__(self, key, value)

    def _get_key(self, key):
        ''' get the key for a given index'''
        # check for out of bounds
        l = len(self)
        if l - 1 < key or key < -l : raise IndexError("index out of range")

        # get the root of the doubly linked list (see the OrderedDict implemenation)
        root = self._OrderedDict__root
        curr = root.next
        act = lambda link : link.next

        # handle -ve indices too
        if key < 0 :
            key += 1
            curr = root.prev
            act = lambda link : link.prev

        # traverse the linked list for our element
        for i in range(abs(key)):
            curr = act(curr)

        # return the key
        return curr.key


# meant to be used interactively as well as programatcially!?!?
class SigSet(object):
    '''holds a set of signals for easy data mgmt, playback and plotting'''
    def __init__(self, *args):
        self.flist = []
        self._signals = OrderedIndexedDict() # ahhh yeah the fancy stuff...

        if args:
            for i in args:
                self._sig[i] = None

        # self._signals = {}
        self._lines = []
        self.fig = None
        # self.add(wave_file_list)

        # FIXME: make scr_dim impl more pythonic! like now...
        self.w, self.h = scr_dim()

        # get the garbarge truck rolling...
        gc.enable()

    def __contains__(self, key):
        # check if in our dict keys
        return key in self._signals

    def __getitem__(self, key):
        return self._signals[key]

    def _load_sig(self, path):
        try:
            print("loading wave file : ",os.path.basename(path))

            # read audio data and params
            sig, self.fs, self.bd = wav_2_np(path)
            # (self.fs, sig) = wavfile.read(self.flist[index])

            amax = 2**(self.bd - 1) - 1
            sig = sig/amax
            self._signals[path] = sig
            print("INFO |->",len(sig),"samples =",len(sig)/self.fs,"seconds @ ",self.fs," Hz")
        except:
            raise Exception("Failed to load wave file!\nEnsure that the wave file exists and is in LPCM format")

    @property
    def show(self):
        '''pretty print the internal path list'''
        #FIXME: throw an error if table is empty
        # if self.flist:
        #     print_table(map(os.path.basename, self.flist))
        if len(self._signals):
            print_table(map(os.path.basename, self._signals.keys()))
        else:
            print("E: no file list exists yet!?...")

    def close_all_figs(self):
        plt.close('all')
        self.fig = None

    def close_fig(self):
        plt.close(self.fig)
        self.fig = None

    def free_cache(self):
        #TODO: make this actually release memory instead of just being a bitch!
        self._signals.clear()
        gc.collect()

    def fullscreen(self):
        if self.mng:
            self.mng.full_screen_toggle()
        else:
            print("no figure handle exists?")

    def vector(self, elem):
        # could be an int-index or path
        if isinstance(elem, str):
            path = elem
        elif isinstance(elem, int):
            path = self.flist[elem]
        else:
            raise IndexError("unsupported index :", elem)

        # path exists and vector loaded
        if path in self._signals.keys():
            # path exists and vector is loaded in mem
            if isinstance(self._signals[path], np.ndarray):
                # print("the file ", self.flist[index], "is already cached in _signals dict!")
                return self._signals[path]

            # path exists but vector not yet loaded
            elif self._signals.get(path) == None:
                self._load_sig(path)
                return self._signals[path]

        # request for an index which doesn't reference a path
        elif path not in self._signals.keys():
            # print("E: you requested an index out of range!")
            raise IndexError("no file path exists for index : " + str(path) + "\n"
                             "Has it been added to your Signal Pack? -> see SigPack.show")
        else:
            raise IndexError("weird stuffs happening heres?!")

    def add(self, p):
        '''Add a wave file path to the SigPack'''
        # '''Can take a single path or a sequence of paths as input'''

        # indices = []
        # paths = iter(paths) # always make paths an iterable

        # a sequence of paths? -> generate look-up indices
        # for p in paths:
        #     print("path = ", p)
        if os.path.exists(p):
            # filename, extension = os.path.splitext(p)
            if p not in self._signals.keys():
                # print("adding file to signal set :\n",p,"\n")
                self.flist.append(p)
                # self._signals[self.flist.index(p)] = None
                self._signals[p] = None
            else:
                print(os.path.basename(p), "is already in our path db -> see grapher.SigPack.show")
        else:
            raise ValueError("path string not valid?!")

        return self.flist.index(p)

    def prettify(self):
        # tighten up the margins
        self.fig.tight_layout(pad=1.03)

    def plot(self, *args):
        ''' can take inputs of ints, ranges, paths, or ....?'''
        # axes = []
        # indices = []

        # for i in args:
        #     if isinstance(i, int):
        #     # TODO: this should be wrapped in a seperate method?
        #         try:
        #             paths.append(self.flist[i])
        #         except:
        #             raise IndexError("E: this Signal Pack does not contain a path for index",i)

        #     elif isinstance(i, str) and i not in self.flist:
        #         self.add(i)
        #     else:
        #         paths.extend([e for e in i])

        # indices.sort()
        # paths = [flist[elem] for elem in indices if type(elem) == int]

        # if len(paths) == 0:
        #     print("E: you must specify integer indices which correspond to paths in self.flist\n"
        #           "see self.show for listing")
        # else:
        return [axis for axis in self.itr_plot(args)]

    # a lazy plotter to save aux space?...doubtful
    def itr_plot(self, items):

    # currently assumes homegenity in type(items)
        # if they're simple int-indices convert to paths now
        # paths = [flist[elem] for elem in items if type(elem) == int]

        paths = []
        for i in items:

            # int-index : get the path we have stored
            if isinstance(i,int):
        #TODO: create a get index from path method...?
                paths.append(self.flist[i])

            # path string : add it if we don't have it
            elif isinstance(i, str):
                self.add(i)
                paths.append(i)

            # some other nested sequence full of int shit?
            else:
                paths.extend([self.flist[e] for e in i])

        # paths = [self.flist[elem] for elem in items if type(elem) == int]

        # if len(paths) == 0:
        # # (i.e. if not ints)
        #     paths = items

            indices = [] # not used here...?

            # add the paths to our db
            # for i in self.add(paths):
            #     indices.append(i)

        # plot the paths...
        for axis, lines in self._plot(paths):
            yield axis

    # plot generator - uses 'makes sense' figure / axes settings
    def _plot(self, keys_itr, start_time=0, samefig=True, title=None):
        axes = {}
        if not isinstance(keys_itr, list):
            keys = [i for i in keys_itr]
        else:
            keys = keys_itr

        # create a new figure and format
        if not samefig or not self.fig:
            self.fig = plt.figure()
            self.mng = plt.get_current_fig_manager()
        else:
            self.fig.clf()

        # set window to half screen size if only one signal
        if len(keys) < 2:
            h = self.h/2
        else:
            h = self.h
        try:
            #pass
            self.mng.resize(self.w, h)
        except:
            raise Exception("unable to resize window!?")

        # self.fig.set_size_inches(10,2)
        # self.fig.tight_layout()

        for icount, key in enumerate(keys):

            # t = np.arange(start_time, len(self.vector(key)) / self.fs, 1/self.fs)
            # set up a time vector
            t = np.linspace(start_time, len(self.vector(key)) / self.fs, num=len(self.vector(key)))
            # print("size of t is ", len(t))

            ax = self.fig.add_subplot(len(keys), 1, icount + 1)
            lines = ax.plot(t, self.vector(key), figure=self.fig)

            font_style = {'size' : 'small'}

            if title == None:
                # ax.set_title(os.path.basename(self.flist[self.flist.index(key)]), fontdict=font_style)
                ax.set_title(os.path.basename(key), fontdict=font_style)
            else:
                ax.set_title(title, fontdict=font_style)

            ax.set_xlabel('Time (s)', fontdict=font_style)
            yield (ax, lines)

    @property
    def get_figure():
        return self.fig

    def find_wavs(self, sdir):
        self.flist = file_scan('.*\.wav$', sdir)
        for i, path in enumerate(self.flist):
            self._signals[i] = None
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

def print_table(itr, field_header=['vector files'], delim='|'):

    itr = [i for i in itr]
    max_width = max(len(field) for field in itr)
    widths = iter(lambda:max_width, 1) # an infinite width generator

    # print field title/headers
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
            str_paths = [os.path.abspath(b.decode()) for b in paths]
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

    # bit depth calc
    bd = wf.getsampwidth() * 8
    frames = wf.readframes(wf.getnframes())

    # hack to read data using array protocol type string
    dt = np.dtype('i' + str(wf.getsampwidth()))
    sig = np.fromstring(frames, dtype=dt)
    wf.close()
    return (sig, fs, bd)

def scr_dim():
    #TODO: find a more elegant way of doing this...say using
    # figure.get_size_inches()
    # figure.get_dpi()
    dn = os.path.dirname(os.path.realpath(__file__))
    bres = subprocess.check_output([dn + "/screen_size.sh"])
    dims = bres.decode().strip('\n').split('x')  # left associative
    return tuple([int(i.strip()) for i in dims if i != ''])

# sound4python module ----v
'''
Copyright (C) 2013 dave.crist@gmail.com
edited and extended by tgoodlet@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

try: import tempfile, wave, subprocess, os, signal, struct, threading, sys#, contextlib
except ImportError as imperr : print(imperr)

# globals

# audio app cmds
snd_utils = {'sox': ['sox','-','-d']}

# but Popen uses the alias DEVNULL anyway...?
FNULL = open(os.devnull,'w')

def launch_without_console(args, strm_output=False):
    """Launches args windowless and waits until finished"""

    startupinfo = None

    if 'STARTUPINFO' in dir(subprocess):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if strm_output:

        # creat process
        p = subprocess.Popen(args,
                         bufsize=1,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         # stderr=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         startupinfo=startupinfo)

        # create a thread to handle app stream parsing
        t = threading.Thread( target=run, kwargs={'proc': p} ) #, q))
        t.daemon = True  # thread dies with program
        t.start()
        # state.join()
        return p

    else:
        return subprocess.Popen(args,
                                stdin=subprocess.PIPE,
                                stdout=FNULL,
                                # stderr=FNULL,
                                startupinfo=startupinfo)
# sound player
def sound(itr, fs, bitdepth=16, start=0, stop=None,
          app = 'sox',
          autoscale=True,
          level =-18.0,        # volume in dBFS
          output=False):
    try:
        import numpy as np
        foundNumpy = True
    except ImportError as imperr:
        foundNumpy = False;
        print(imperr)

    print("playing from", start,"until", stop)
    # set start sample
    start = start * fs
    # set stop sample
    if not stop:
        stop = len(itr)
    else:
        stop = stop * fs

    # slicing should work for most itr
    itr = itr[start:stop]

    #for now, assume 1-D iterable
    mult = 1
    if autoscale:
        # multiplier to scale signal to max volume at preferred bit depth
        mval = 2**(bitdepth - 1)
        A = 10**(level/20.)
        mult = A * float(mval) / max(itr)

    #create file in memory
    memFile = tempfile.SpooledTemporaryFile()

    # create wave write objection pointing to memFile
    waveWrite = wave.open(memFile,'wb')
    waveWrite.setsampwidth(2)        # int16 default
    waveWrite.setnchannels(1)        # mono  default
    waveWrite.setframerate(fs)       # 8kHz  default
    wroteFrames = False

    # try to create sound from NumPy vector
    if foundNumpy:
        if type(itr) == np.array:
            if itr.ndim == 1 or itr.shape.count(1) == itr.ndim - 1:
                waveWrite.writeframes( (mult*itr.flatten()).astype(np.int16).tostring() )
                wroteFrames=True

        else: # we have np, but the iterable isn't a vector
            waveWrite.writeframes( (mult*np.array(itr)).astype(np.int16).tostring() )
            wroteFrames=True

    if not wroteFrames and not foundNumpy:
        # python w/o np doesn't have "short"/"int16", "@h" is "native,aligned short"
        waveWrite.writeframes( struct.pack(len(itr)*"@h", [int(mult*itm) for  itm in itr]) )
        wroteFrames=True

    if not wroteFrames:
        print("E: Unable to create sound.  Only 1D numpy arrays and numerical lists are supported.")
        waveWrite.close()
        return None

    #configure the file object, memFile, as if it has just been opened for reading
    memFile.seek(0)

    # getting here means wroteFrames == True
    print("\nAttempting to play a mono audio stream of length "
          "{0:.2f} seconds\n({1:.3f} thousand samples at sample "
          "rate of {2:.3f} kHz)".format(1.0*len(itr)/fs, len(itr)/1000., int(fs)/1000.))
    try:
        # look up the cmdline listing
        cmd = snd_utils[app]
        # launch the process
        p = launch_without_console(cmd, strm_output=output)

    except:
        print("\nE: Unable to launch sox.")
        print("E: Please ensure that sox is installed and on the path.")
        print("E: Try 'sox -h' to test sox installation.")
        waveWrite.close()
        return None

    try:
        p.communicate(memFile.read())
        print(app,"communication completed...")
        # p.wait()

    except:
        print("E: Unable to send in-memory wave file to stdin of sox subprocess.")
        waveWrite.close()
        return None
#os.kill(p.pid,signal.CTRL_C_EVENT)
#end def sound(itr,samprate=8000,autoscale=True)

# # threaded class to hold cursor state info
# class SoxState(thread.
# class ProcOutput(threading.Thread):
#     def __init__(self, proc):
#         self.p = proc
#         self.stdout = None
#         self.stderr = None
#         threading.Thread.__init__(self)
# def print_stdout():
#     for line in sys.stdout.readline():
#         print line

def run(proc): #, queue):
    # Poll process for new output until finished
    for b in unbuffered(proc, stream='stderr'):
        # print("next line...\n")
        print(b)

    # stream = proc.stderr
    # nbytes = 1
    # # stream = getattr(proc, stream)
    # read = lambda : os.read(stream.fileno(), nbytes)
    # while proc.poll() is None:
    #     out = []
    #     # read a byte
    #     try:
    #         last = read().decode()
    #         print(last)
    #     # in case the proc closes and we don't catch it with .poll
    #     except ValueError:
    #         print("finished piping...")
    #         break

        # try:
        #     # read a byte at a time until eol...
        #     while last not in newlines:
        #         out.append(last)
        #         last = read().decode()
        # except:
        #     print("finished piping...")
        #     break
        # else:
        #     print(out)
            # out.clear()

# Unix, Windows and old Macintosh end-of-line
newlines = ['\n', '\r\n', '\r']
def unbuffered(proc, stream='stdout', nbytes=1):
    stream = getattr(proc, stream)
    read = lambda : os.read(stream.fileno(), nbytes)
    while proc.poll() is None:
        out = []
        # read a byte
        last = read().decode()
        try:
            # read bytes until eol...
            while last not in newlines:
                out.append(last)
                last = read().decode()
            if len(out) == 0: continue
        # in case the proc closes and we don't catch it with .poll
        except ValueError:
            print("finished piping...")
            break
        else:
            # yield ''.join(out)
            yield out
            # out.clear()

# select values from an itr by index
def itr_iselect(itr, *indices):
    i_set = set(indices)
    return (e for (i, e) in enumerate(itr) if i in i_set)

def test():
    # example how to use the lazy plotter
    ss = SigSet()
    ss.find_wavs('/home/tyler/code/python/wavs/')
    # wp.plot(0)
    return ss

def lazy_test():
    pass

if __name__ == '__main__':
    sp = test()
