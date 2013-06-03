# sound4python module

'''
Copyright (C) 2013 dave.crist@gmail.com
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

try: import tempfile, wave, subprocess, os, signal, struct
except ImportError as imperr : print(imperr)

# globals
FNULL = open(os.devnull,'w')

def launchWithoutConsole(args, output=False):
    """Launches args windowless and waits until finished"""

    startupinfo = None

    if 'STARTUPINFO' in dir(subprocess):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if output:
        return subprocess.Popen(args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                startupinfo=startupinfo)
    else:
        return subprocess.Popen(args,
                                stdin=subprocess.PIPE,
                                stdout=FNULL,
                                stderr=FNULL,
                                startupinfo=startupinfo)
# sox sound player
def sound(itr, fs, bitdepth=16,
          start=0, stop=None,
          autoscale=True,
          level=-12,
          output=False):
    try:
        import numpy as np
        foundNumpy = True
    except ImportError as imperr:
        foundNumpy = False;
        print(imperr)

    # set stop sample
    if not stop:
        stop = len(itr)

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
        print("\nAttempting to play a mono audio stream of length"
              "{0:.2f} seconds\n({1:.3f} thousand samples\nat sample"
              "rate of {2:.3f} kHz)".format(1.0*len(itr)/fs, len(itr)/1000., int(fs)/1000.))

        p = launchWithoutConsole(['sox','-','-d'])

    except:
        print("E: Unable to launch sox.")
        print("E: Please ensure that sox is installed and on the path.")
        print("E: Try 'sox -h' to test sox installation.")
        waveWrite.close()
        return None

    try:
        p.communicate(memFile.read())
        # p.wait()
    except:
        print("E: Unable to send in-memory wave file to stdin of sox subprocess.")
        waveWrite.close()
        return None
    #os.kill(p.pid,signal.CTRL_C_EVENT)
#end def sound(itr,samprate=8000,autoscale=True)
