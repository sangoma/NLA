# sound4python module

'''
Copyright (C) 2013 dave.crist@gmail.com
(with small additions by tgoodlet@gmail.com)

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

try: import tempfile, wave, subprocess, os, signal, struct, threading, sys
except ImportError as imperr : print(imperr)

# globals
# but Popen uses the alias DEVNULL anyway...?
FNULL = open(os.devnull,'w')

def launchWithoutConsole(args, output=False):
    """Launches args windowless and waits until finished"""

    startupinfo = None

    if 'STARTUPINFO' in dir(subprocess):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # if output:
    #     std_out = std_err = subprocess.PIPE
    # else:
    #     std_out = std_err = FNULL

    # return subprocess.Popen(args,
    #                             stdin=subprocess.PIPE,
    #                             stdout=std_out,
    #                             stderr=std_err,
    #                             # shell=False,
    #                             startupinfo=startupinfo)
    if output:
        return subprocess.Popen(args,
                                # bufsize=1,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                # stderr=subprocess.PIPE,
                                startupinfo=startupinfo)
    else:
        return subprocess.Popen(args,
                                stdin=subprocess.PIPE,
                                stdout=FNULL,
                                stderr=FNULL,
                                startupinfo=startupinfo)
# sound player
def sound(itr, fs, bitdepth=16,
          start=0, stop=None,
          autoscale=True,
          level =-18.0,        # volume in dBFS
          output=False):
    try:
        import numpy as np
        foundNumpy = True
    except ImportError as imperr:
        foundNumpy = False;
        print(imperr)

    # set start sample
    start = start * fs
    # set stop sample
    if not stop:
        stop = len(itr)
    else:
        stop = stop * fs

    # slicing should work for most itr
    itr = itr[start:stop]
    print('start is', start)
    print("len of itr is", len(itr))

    #for now, assume 1-D iterable
    mult = 1
    if autoscale:
        # multiplier to scale signal to max volume at preferred bit depth
        mval = 2**(bitdepth - 1)
        A = 10**(level/20.)
        mult = A * float(mval) / max(itr)

    #create file in memory
    #with tempfile.SpooledTemporaryFile() as memFile:
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

    try:
        # getting here means wroteFrames == True
        print("\nAttempting to play a mono audio stream of length "
              "{0:.2f} seconds\n({1:.3f} thousand samples at sample "
              "rate of {2:.3f} kHz)".format(1.0*len(itr)/fs, len(itr)/1000., int(fs)/1000.))

        # p = launchWithoutConsole(['sox','-','-d'], output=True)

        tf = tempfile.TemporaryFile(buffering=8)
        p = subprocess.Popen(['sox','-','-d'],
                                # bufsize=0,
                                stdin=subprocess.PIPE,
                                # stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        # from queue import Queue, Empty  # python 3.x
        # q = Queue()

        # t = threading.Thread( target=run, kwargs={'p': p} ) #, q))
        # t.daemon = True  # thread dies with program
        # # state = ProcOutput(p)
        # t.start()

        # ... do other things here

        # read line without blocking
        # try:  line = q.get_nowait() # or q.get(timeout=.1)
        # except Empty:
        #     print('no output yet')
        # else: # got line
        #     print("printing line...")
        #     print(line)
            # ... do something with line

        # state.join()

    except:
        print("\nE: Unable to launch sox.")
        print("E: Please ensure that sox is installed and on the path.")
        print("E: Try 'sox -h' to test sox installation.")
        waveWrite.close()
        return None

    try:
        p.communicate(memFile.read())
        p.wait()

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

    # p = subprocess.Popen('rsync -av /etc/passwd /tmp'.split(),
    #         shell=False,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE)
    # self.stdout, self.stderr = p.communicate()
    # setinel is "" (search for blank line...)
    # for line in iter(sys.stdin.readline, ""):
    # for line in iter(proc.stderr.readline, b''):

    # proc.stderr.flush()
    # for line in iter(proc.stderr.readline, b''):
    #     # queue.put(line)
    #     print(line)

def run(p): #, queue):
    # while True:
        # line = p.stderr.readline()
        # if not line:
        #     break
        for line in unbuffered(p):
            print(line)
        # print("yes maam!")
    # Poll process for new output until finished
        # while True:
        #     nextline = p.stdout.readline()
        #     if nextline == b'' and p.poll() != None:
        #         break
        #     queue.put(nextline)
        #     print(nextline)
        #     sys.stdout.write(nextl)
        #     sys.stdout.flush()
    # for line in f.readline():


import contextlib
# Unix, Windows and old Macintosh end-of-line
newlines = ['\n', '\r\n', '\r']
def unbuffered(proc, stream='stdout'):
    stream = getattr(proc, stream)
    with contextlib.closing(stream):
        while True:
            out = []
            # read a byte
            last = stream.read(1)

            # Don't loop forever
            if last == '' and proc.poll() is not None:
                break

            # read a byte at a time...
            while last not in newlines:
                out.append(last)
                last = stream.read(1)
            out = ''.join(out)
            yield out
