#! python2
#coding=utf-8
from __future__ import division

import numpy as np
import wave
import math

f=wave.open('input.wav','rb')
nchannels, sampwidth, framerate, nframes = f.getparams()[:4]
data=np.fromstring(f.readframes(nframes),np.short)
f.close()
data.shape=-1,nchannels
data=data.T

import midi
trk=midi.Track()
trk.append(midi.ProgramChangeEvent(tick=0, channel=0, data=[34]))
ptr=midi.Pattern(tracks=[trk],resolution=500,format=0)
rate=1500

class Notes:
    _delta_time=int(rate/framerate*1000)

    def __init__(self):
        self.items=[]
        self.curtime=0
        self.maxsound=1

    @staticmethod
    def _fixvel(pitch,vel):
        return vel#**.75 #if pitch>=64 else (pitch-20)/44*vel

    def newtick(self):
        self.curtime+=self._delta_time

    def insert(self,vel,pitch):
        vel=self._fixvel(pitch,vel)
        self.items.append([True,self.curtime,vel,pitch])
        self.items.append([False,self.curtime+.9*self._delta_time,vel,pitch])
        self.maxsound=max(self.maxsound,vel)

    def _toevt(self,evt,basetime):
        if evt[2]*255/self.maxsound>8:
            if evt[0]:
                return midi.NoteOnEvent(tick=int(evt[1]-basetime),velocity=int(evt[2]*255/self.maxsound),pitch=evt[3])
            else:
                return midi.NoteOffEvent(tick=int(evt[1]-basetime),pitch=evt[3])

    def fetchall(self):
        srted=sorted(self.items,key=lambda x:x[1])
        yield self._toevt(srted[0],0)
        for i in range(1,len(srted)):
            yield self._toevt(srted[i],srted[i-1][1])

def tomidi(f):
    if f<27:
        return 21
    elif f>4300:
        return 108
    return int(12*math.log(f/440,2)+69+.5)

freq=[tomidi(framerate/(rate-1)*n) for n in range(rate)]

notes=Notes()
for start in range(0,nframes,rate):
    res={freq[k]:v for k,v in enumerate(abs(np.fft.fft(data[0][start:start+rate]))) if freq[k]}
    notes.newtick()
    for ind,sound in sorted(res.items(),key=lambda x:x[1],reverse=True)[:10]:
        notes.insert(sound,ind)

for item in notes.fetchall():
    if item is not None:
        trk.append(item)

trk.append(midi.EndOfTrackEvent(tick=1))
midi.write_midifile('out.mid',ptr)
