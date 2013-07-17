#!/usr/bin/env python3
'''
Visig   - visualize and animate signals using mpl

author  : Tyler Goodlet
email   : tgoodlet@gmail.com
website : http://tgoodlet.github.com
license : BSD
Please feel free to use and modify this, but keep the above information.
'''

# TODO;
# - consider using sox conversion in this module so we can open
#   arbitrarly formatted audio files as numpy arrays
# - 'Signal' class which is delegated all data unpacking and metadata maintenance
# - animation for simple playback using a cursor on the chosen axes (add mixing?)
# - animation for rt spectrum
# - mechanism to animate arbitrary metric computations in rt
# - capture sreen dimensions using pure python
# - create a callback mechnism which interfaces like a rt algo block and
#   allows for metric animations used for algo development

# required libs
from imp import reload
import numpy as np

# mpl
# import matplotlib
# matplotlib.use('Qt4Agg')
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt4 import FigureManagerQT as FigureCanvas
# from matplotlib.backends.backend_qt4 import new_figure_manager_given_figure
from matplotlib.backends import pylab_setup
_backend_mod, new_figure_manager, draw_if_interactive, _show = pylab_setup()

import matplotlib.animation as animation
# import matplotlib.pyplot as plt
# from matplotlib import pylab

#from scipy.io import wavfile
# from scipy import signal
# from scipy import fftpack
import subprocess, os, gc
from collections import OrderedDict, deque

# like it sounds : an ordered, int subscriptable dict
class OrderedIndexedDict(OrderedDict):
    def __getitem__(self, key):
        #FIXME: how to handle slices?
        #(it's weird since we always have to check first and using the list...)
        if isinstance(key, slice ):
            print("you've passed a slice! with start",key.start,"and stop",key.stop)
            return list(self.values())[key]

        # if it's already mapped get the value
        elif key in self:
            return OrderedDict.__getitem__(self, key)

        # FIXME: is this the fastest way to implement this?
        # if it's an int, iterate the linked list and return the value
        elif isinstance(key, int):
            return self[self._get_key(key)]
            # return self._setget_value(key)

    def __setitem__(self, key, value):
        # don't give me ints bitch...(unless you're changing a value)
        if isinstance(key, int):# raise KeyError("key can not be of type integer")
            key = self._get_key(key)
        OrderedDict.__setitem__(self, key, value)

    def _get_key(self, key):
        ''' get the key for a given index'''
        # check for out of bounds
        l = len(self)
        if l - 1 < key or key < -l :
            raise IndexError("index out of range, len is " + str(l))

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

class SigMap(object):
    '''
    Wraps an ordered map of signals for easy data/vector mgmt, playback and visualization
    The mpl figure is managed as a singleton and subplots are used whenever viewing multiple signals
    The main intent is to avoid needless figure clutter and boilerplate lines found in sig proc scripts

    Use this class interactively (IPython) as well as programatically
    '''
    def __init__(self, *args):
        self._signals = OrderedIndexedDict() # what's underneath...
        # unpack any file names that might have been passed initially
        if args:
            for i in args:
                self._sig[i] = None

        # mpl stateful objs
        # self._lines  = []
        self._fig      = None
        self._mng      = None
        self._cur_sig  = None
        self._axes_set = set()

        # to be updated by external thread
        self._cur_sample = 0
        self._cur_sig   = None

        # animation state
        self._provision_anim = lambda : None
        self._anim_func      = None
        self._frames_gen     = None
        self._anim_fargs     = None
        self._anim_sig_set   = set()
        self._time_elapsed   = 0

        # animation settings
        self._fps = 5   # determines the resolution for animated metrics (i.e. window size)

        # FIXME: make scr_dim impl more pythonic!
        self.w, self.h = scr_dim()
        # get the garbarge truck rolling...
        gc.enable()

    # FIXME: is this superfluous?
    # delegate as much as possible to the oid
    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            return getattr(self._signals, attr)

    def __setitem__(self, *args):
        return self._signals.__setitem__(*args)

    def __getitem__(self, key):
        '''lazy loading of signals and delegation to the oid'''
        # path exists in our set
        if isinstance(self._signals[key], np.ndarray): pass
        # path exists but signal not yet loaded
        else: self._load_sig(key)
        return self._signals[key]

    def __del__(self):
        self.kill_mpl()
        self.free_cache()

    # TODO: move to Signal class
    def _load_sig(self, path):
        if isinstance(path, int):
            path = self._signals._get_key(path)
        if path in self._signals:
            #TODO: loading should be completed by 'Signal' class (i.e. format specific)
            try:
                print("loading wave file : ",os.path.basename(path))
                # read audio data and params
                sig, self.fs, self.bd = wav_2_np(path)
                # (self.fs, sig) = wavfile.read(self.flist[index])

                amax = 2**(self.bd - 1) - 1
                sig = sig/amax
                self._signals[path] = sig
                print("INFO |->",len(sig),"samples =",len(sig)/self.fs,"seconds @ ",self.fs," Hz")
                return path
            except:
                raise Exception("Failed to load wave file!\nEnsure that the wave file exists and is in LPCM format")
        else: raise KeyError("no entry in the signal set for key '"+str(path)+"'")

    def _sig2axis(self, sig_key=None):
        '''return rendered axis corresponding to a the requested signal'''
        #FIXME: in Signal class we should assign the axes
        # on which a signal is drawn to avoid this hack?
        if not sig_key: sig_key = self._cur_sig
        sig = self[sig_key]
        try:
            for ax in self.figure.get_axes():
                for line in ax.get_lines():
                    if sig in line.get_ydata():# continue
                        return ax
                    else:
                        return None
        except ValueError:      # no easy way to compare vectors?
            return None
            # return ax
        # else:
        #     return self._sig2axis(self._cur_sig)

    def _prettify(self):
        '''pretty the figure in sensible ways'''
        # tighten up the margins
        self._fig.tight_layout(pad=1.03)

    def _init_anim(self):
        '''
        in general we provision as follows:
        1) check if the 'current signal(s)' (_cur_signal) is shown on a figure axis
        2) if not (re-)plot them
        3) return the basline artists which won't change after plotting (usually time and amplitude)
        '''
        # axes = [self._sig2axis(key) for key in self._anim_sig_set]
        ax = self._sig2axis(self._cur_sig)
        if not ax:
            ax = self.plot(self._cur_sig)
        #4) do addional steps using self._provision_anim
        # self._provision_anim()
        # return the artists which won't change during animation (blitting)
        return ax.get_lines()
        # line = vline(axis, time, colour=green)

    def _do_fanim(self):
        '''run the function based animation once
        this blocks until the the animation is complete when using an interactive fe'''
        if self._anim_func:
            anim = animation.FuncAnimation(self.figure,
                                           self._anim_func,
                                           frames=self._frames_gen,
                                           init_func=self._init_anim,
                                           fargs=self._anim_fargs,
                                           interval=1//self._fps*1000,
                                           repeat=False)

            # self._animations.appendleft(anim)
        else: raise RuntimeError("no animation function has been set!")

    def sound(self, key, **kwargs):
        '''JUST play sound'''
        sig = self[key]
        sound4python(sig, sig.fs, **kwargs)

    def play(self, key):
        '''play sound + do mpl animation with a playback cursor'''
        # sig = self[key]
        self._cur_sig = key
        ax = self._sig2axis(key)
        self._anim_fargs = cursor(ax, 0)
        # set animator routine
        self._anim_func = self._set_cursor
        # set the frame iterator
        self._frames_gen = self._audio_time_gen

        # t = threading.Thread( target=buffer_proc_stream, kwargs={'proc': p, 'callback': callback} ) #, q))
        # t.daemon = True  # thread dies with program
        # t.start()
        self._do_fanim()

    def _set_cursor(self, sample_time, *fargs):
        '''
        perform animation step using the frame number and cursor line
        cursor artist must be first element in *fargs
        '''
# TODO? place a lock here?
        cursor_line = fargs[0]
        cursor_line.set_data(float(sample_time), [0,1])
        return cursor_line

    def _audio_time_gen(self):
        '''generate the audio sample-time for cursor placement
        on each animation frame'''
        # frame_step = self.fs / self._fps    # samples/frame
        time_step = 1/self._fps
        self._audio_time = 0                # this can be locked out
                                        # FIXME: get rid of this hack job!
        while self._audio_time <= len(self[self._cur_sig]/self.fs):
            yield self._audio_time
            self._audio_time += time_step

    def _cursor_playback(self, sig_key):
        # indicate signal for playback + a visual cursor along axis
        # if the signal is not present in the current subplot set
        # then replot with only that signal
        pass

    def _show_corpus(self):
        '''pretty print the internal path list'''
        try: print_table(map(os.path.basename, self._signals.keys()))
        except: raise ValueError("no signal entries exist yet!?...add some first")

    # convenience attrs
    figure      = property(lambda self: self._fig)
    mng         = property(lambda self: self._mng)
    flist       = property(lambda self: [f for f in self.keys()])
    show_corpus = property(lambda self : self._show_corpus())
    def get(self, key): self.__getitem__(key)

    def kill_mpl(self):
        # plt.close('all')
        self.mng.destroy()
        self._fig = None

    def close(self):
        if self._fig:
            # plt.close(self._fig)
            self._fig.close()
            self._fig = None #FIXME: is this necessary?

    def clear(self):
        #FIXME: make this actually release memory instead of just being a bitch!
        self._signals.clear()
        gc.collect()

    def fullscreen(self):
        '''convenience func to fullscreen if using a mpl gui fe'''
        if self._mng:
            self._mng.full_screen_toggle()
        else:
            print("no figure handle exists?")

    def add_path(self, p):
        '''
        Add a data file path to the SigMap
        Can take a single path string or a sequence as input
        '''
        if os.path.exists(p):
            # filename, extension = os.path.splitext(p)
            if p not in self:#._signals.keys():
                self[p] = None
            else:
                print(os.path.basename(p), "is already in our path db -> see grapher.SigPack.show()")
        else:
            raise ValueError("path string not valid?!")

    def plot(self, *args, **kwargs):
        '''
        can take inputs of ints, ranges or paths
        meant to be used as an interactive interface...
        returns a either a list of axes or a single axis
        '''
        axes = [axis for axis,lines in self.itr_plot(args, **kwargs)]
        self._prettify()
        if len(axes) < 2:
            axes = axes[0]
        # self.figure.show() #-> only works when using pyplot
        return axes

    def itr_plot(self, items, **kwargs):
        '''
        a lazy plotter to save aux space?...doubtful
        should be used as the programatic interface to _plot
        '''
        paths = []
        for i in items:
            # path string, add it if we don't have it
            if isinstance(i, str) and i not in self:
                self.add_path(i)
                paths.append(i)
            elif isinstance(i, int):
                paths.append(self._get_key(i)) # delegate to oid (is this stupid?)

        # plot the paths (composed generator)
        # return (axis,lines for axis,lines in self._plot(paths, **kwargs))
        for axis,lines in self._plot(paths, **kwargs):
            yield axis, lines

    def _plot(self, keys_itr, start_time=0, time_on_x=True, singlefig=True, title=None):
        '''
        plot generator - uses 'makes sense' figure / axes settings
        inputs: keys_itr -> must be an iterator over path names in self.keys()
        '''
        # FIXME: there is still a massive memory issue when making multiple plot
        # calls and I can't seem to manage it using the oo-interface or
        # pyplot (at least not without closing the figure all the time...lame)

        if isinstance(keys_itr, list):
            keys = keys_itr
        else:
            keys = [i for i in keys_itr]

        # create a new figure and format
        if not singlefig or not (self._fig and self._mng):

            # using mpl/backends.py pylab setup (NOT pylab)
            self._mng = new_figure_manager(1)
            self._mng.set_window_title('visig')
            self._fig = self._mng.canvas.figure

            # using pylab
            # pylab and pyplot seem to be causing mem headaches?
            # self._fig = pylab.figure()
            # self._mng = pylab.get_current_fig_manager()

            # using pyplot
            # self.fig = plt.figure()
            # self._mng = plt.get_current_fig_manager()

            # using oo-api directly
            # self._fig = Figure()
            # self._canvas = FigureCanvas(self._fig)
            # self._mng = new_figure_manager(1, self._fig)
            # self._mng = new_figure_manager_given_figure(1, self._fig)

        else:
            # for axis in self.figure.get_axes():
            #     axis.clear()
            #     gc.collect()
                # for line in axis.get_lines():
                    # line.clear()
                    # gc.collect()
            self.figure.clear()
            gc.collect()

        # draw fig
        # TODO: eventually detect if a figure is currently shown?
        draw_if_interactive()

        # set window to half screen size if only one signal
        if len(keys) < 2: h = self.h/2
        else: h = self.h
        # try:
        self._mng.resize(self.w, h)
        # except: raise Exception("unable to resize window!?")
        # self._fig.set_size_inches(10,2)
        # self._fig.tight_layout()

        # title settings
        font_style = {'size' : 'small'}

        # main plot loop
        for icount, key in enumerate(keys):
            # always set 'curr_sig' to last plotted
            sig = self._cur_sig = self[key]
            slen  = len(sig)

            # set up a time vector and plot
            t     = np.linspace(start_time, slen / self.fs, num=slen)
            ax    = self._fig.add_subplot(len(keys), 1, icount + 1)
            # maintain a set of current signals present on the active axes
            # self._axes_set.add(sig)
            lines = ax.plot(t, sig, figure=self._fig)
            ax.set_xlabel('Time (s)', fontdict=font_style)

            if title == None: title = os.path.basename(key)
            ax.set_title(title, fontdict=font_style)

            # ax.figure.canvas.draw()
            yield (ax, lines)

    def find_wavs(self, sdir):
        '''find all wav files in a dir'''
        # self.flist = file_scan('.*\.wav$', sdir)
        for i, path in enumerate(file_scan('.*\.wav$', sdir)):
            self[path] = None
            print("found file : ",path)
        print("found", len(self.flist), "files")

    # example callback
    def print_cb(self, *fargs):
        for i in fargs:
            print(i)

    def register_callback(self):
        pass

class Signal(object):
    '''
    base class for loading arbitray data files into np arrays
    normal procedure is to convert to wav using a system util
    and then load from wav to numpy array
    '''

    def __init__(self, file_path):
        self._fs = None
        self._signal = None
        self._detect_fmt(file_path)
        pass

    def _load_sig(self, path):
        pass

    def __getattr__(self):
        return getattr(self._signal, attr)

    def _detect_fmt(selft):
        raise NotImplementedError('Needs to be implemented by subclasses to'
                                  ' actually detect file format.')

    def _load_sig(self):
        raise NotImplementedError('Needs to be implemented by subclasses to'
                                  ' actually load a signal.')

import wave
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

def cursor(axis, time, colour='r'):
    '''add a vertical line @ time (...looks like a cursor)
    here the x axis should be a time vector
    such as created in SigMap._plot
    the returned line 'l' can be set with l.set_data([xmin, xmax], [ymin, ymax])'''
    return axis.axvline(x=time, color=colour)

def label_ymax(axis, label):
    '''add an optional label to the line @ ymax'''
    # use ylim for annotation placement
    mx = max(axis.get_ylim())
    ret = axis.annotate(label,
                  xy=(time, mx),
                  xycoords='data',
                  xytext=(3, -10),
                  textcoords='offset points')
                  # arrowprops=dict(facecolor='black', shrink=0.05),
                  # horizontalalignment='right', verticalalignment='bottom')
    return ret

def lines_max_y(axis):
    # use max value from the available lines for annotation placement
    lines = axis.get_lines()
    mx = 0
    for line in lines:
        lm = max(line.get_ydata())
        if lm > mx:
            mx = lm
    return mx

def print_table(itr, field_header=['signal files'], delim='|'):
    '''pretty print iterable in a column'''
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

def scr_dim():
    #TODO: find a more elegant way of doing this...say using
    # figure.get_size_inches()
    # figure.get_dpi()
    dn = os.path.dirname(os.path.realpath(__file__))
    bres = subprocess.check_output([dn + "/screen_size.sh"])
    dims = bres.decode().strip('\n').split('x')  # left associative
    return tuple([int(i.strip()) for i in dims if i != ''])


# from the sound4python module
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

try: import tempfile, wave, signal, struct, threading, sys#, contextlib
except ImportError as imperr : print(imperr)

# TODO: make the subclasses
class SndApp(object):
    '''
    base class for sound app wrappers
    sound app can be a single command or can be a class
    if app is a command opt_list is it's arguments if a class then it's __init__ args
    '''
    def __init__(self, app, opt_list=None, parser=None):
        # if we get a class
        if isinstance(app, type):
            self = app.__init__(opt_list, parser)
        elif isinstance(app, str):
            self.cmd_line = []
            self.cmd_line.append(app)
            self.cmd_line.extend(opt_list)

        if parser:
            self._parser = parser

    def analyze(self, f):
        '''sublcass method to analyze a file'''
        raise NotImplementedError("must implement the file analysis in the child class!")

# app parser funcs
def parse_sox_cur_time(s):
    '''
    s : string or buffer?
    parser funcs must take in a string or buffer and provide a string output
    '''
    val = s.strip('\n')
    return val

def parse_aplay(s):
    pass

def parse_sndfile(s):
    pass

# audio (linux) app cmds
# TODO:
# - check for app existence in order
# - extend the SndApp class to contain method calls for generic analysis
#   and multichannel playback (multiprocessing module?)
# - should this class contain a parser plugin mechanism?

snd_utils            = OrderedDict()
snd_utils['sox']     = SndApp('sox', opt_list=['-','-d'], parser=parse_sox_cur_time)
snd_utils['aplay']   = SndApp('aplay', opt_list=['-vv', '--'], parser=parse_aplay)
snd_utils['sndfile'] = SndApp('sndfile-play', opt_list=['-'], parser=parse_sndfile)

def get_snd_app():
    '''get the first available sound app'''
    pass
    # for app in snd_utils:
    #     arg0 = app.

def sound4python(itr, fs, bitdepth=16, start=0, stop=None,
          app_name='sox',
          autoscale=True,
          level =-18.0,
          callback=None):
    '''
    a python sound player which delegates to a system (Linux) audio player

    params:
            itr          : input python iterable for playback
            fs           : sample rate of data
            start/stop   : start/stop vector indices
            app_name     : system app of type SndApp used for playback
                           current available options are sox, alsa play, and lib-sndfile play
            autoscale    : indicates to enable playback at the provided 'level'
            level        : volume in dBFS
            callback     : will be called by the snd app with (parser) output passing in 'fargs'
    '''
# TODO: move these imports out of here?
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
    # mult = 1
    if autoscale:
        # multiplier to scale signal to max volume at preferred bit depth
        mxval = 2**(bitdepth - 1)           # signed 2's comp
        A = 10**(level/20.)                 # convert from dB
        mult = A * float(mxval) / max(itr)

    #create file in memory
    memFile = tempfile.SpooledTemporaryFile()

    # create wave write objection pointing to memFile
    waveWrite = wave.open(memFile,'wb')
    waveWrite.setsampwidth(bitdepth/8)  # int16 default
    waveWrite.setnchannels(1)           # mono  default
    waveWrite.setframerate(fs)
    wroteFrames = False

    # utilize appropriate data type
    dt = np.dtype('i' + str(bitdepth))
    # try to create sound from NumPy vector
    if foundNumpy:
        if type(itr) == np.array:
            if itr.ndim == 1 or itr.shape.count(1) == itr.ndim - 1:
                waveWrite.writeframes( (mult*itr.flatten()).astype(dt).tostring() )
                wroteFrames=True

        else: # we have np, but the iterable isn't a vector
            waveWrite.writeframes( (mult*np.array(itr)).astype(dt).tostring() )
            wroteFrames=True

    if not wroteFrames and not foundNumpy:
        # FIXME: how to set playback bitdepth dynamically using this method?
        # -> right now this is hardcoded to bd=16
        # python w/o np doesn't have "short"/"int16", "@h" is "native,aligned short"
        waveWrite.writeframes( struct.pack(len(itr)*"@h", [int(mult*itm) for  itm in itr]) )
        wroteFrames=True

    if not wroteFrames:
        print("E: Unable to create sound.  Only 1D numpy arrays and numerical lists are supported.")
        waveWrite.close()
        return None

    # configure the file object, memFile, as if it has just been opened for reading
    memFile.seek(0)

    # getting here means wroteFrames == True
    print("\nAttempting to play a mono audio stream of length "
          "{0:.2f} seconds\n({1:.3f} thousand samples at sample "
          "rate of {2:.3f} kHz)".format(1.0*len(itr)/fs, len(itr)/1000., int(fs)/1000.))
    try:
        # look up the cmdline listing
        app = snd_utils[app_name]

        # launch the process parsing std streams output if requested
        p = launch_without_console(app.cmd_line, strm_output=True)

        if callback:
            # create a thread to handle app output stream parsing
            # TODO: make thread a class with more flexibility
            t = threading.Thread( target=buffer_proc_stream, kwargs={'proc': p, 'callback': callback} ) #, q))
            t.daemon = True  # thread dies with program
            t.start()
            # state.join()

    except:
        # FIXME: make this an appropriate exception
        print("\nE: Unable to launch sox.")
        print("E: Please ensure that sox is installed and on the path.")
        print("E: Try 'sox -h' to test sox installation.")
        waveWrite.close()
        return None
    try:
        # deliver data to process (normally a blocking action)
        p.communicate(memFile.read())
        print(app,"communication completed...")
        # p.wait()

    except:
        # FIXME: make this an appropriate exception
        print("E: Unable to send in-memory wave file to stdin of sox subprocess.")
        waveWrite.close()
        return None
#os.kill(p.pid,signal.CTRL_C_EVENT)
#end def sound(itr,samprate=8000,autoscale=True)

# but Popen uses the alias DEVNULL anyway...? (legacy...damn)
FNULL = open(os.devnull,'w')

def launch_without_console(args, strm_output=False):
    """Launches args windowless and waits until finished"""
    startupinfo = None

    if 'STARTUPINFO' in dir(subprocess):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if strm_output:
        # create process
        p = subprocess.Popen(args,
                         # bufsize=1,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         startupinfo=startupinfo)
        return p
    else:
        return subprocess.Popen(args,
                                stdin=subprocess.PIPE,
                                stdout=FNULL,
                                # stderr=FNULL,
                                startupinfo=startupinfo)

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

def buffer_proc_stream(proc,
                       # deque,
                       std_stream='stderr',
                       parser=lambda arg : arg,
                       callback=print):
    '''Poll process for new output until finished pass to callback
       parser is an identity map if unassigned'''

    for b in unbuffered(proc, stream=std_stream):
        # deque.appendleft(parser(b))
        callback(parser(b))

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
    '''
    down and dirty unbuffered byte stream generator
    which reads the explicit fd
    (since the built-ins weren't working for me)
    '''
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

def _in_ipython():
    try:
        __IPYTHON__
    except NameError:
        return False
    else:
        return True

def ipy():
    '''if possible, launch ipython'''
    if _in_ipython():
        pass
    else:
        print("\nattempting to start the ipython shell...\n")
        try: from IPython import embed
        except ImportError as imperr : print(imperr)
        # start IPython whilst maintaining the current namespace and scope
        return embed()

# TODO: should try out pyunit here..
def test():
    # example how to use the lazy plotter
    ss = SigMap()
    ss.find_wavs('/home/tyler/code/python/wavs/')
    # wp.plot(0)
    return ss

# script interface
if __name__ == '__main__':
    ss = test()
    print("play with instance 'ss'\ne.g. ss.show_corpus...")
    shell = ipy()
