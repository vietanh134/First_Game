import wave, struct, math

sr = 44100

def mk(fn, d, f1, f2, dec, amp, att):
    f = wave.open(fn, 'w')
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(sr)
    for i in range(int(sr*d)):
        t = i/sr
        env = math.exp(-dec*t) * min(1.0, t/att)
        v = (math.sin(2.0*math.pi*f1*t) + math.sin(2.0*math.pi*f2*t))*0.5
        v += 0.2*math.sin(2.0*math.pi*f1*2*t)
        v = max(-1.0, min(1.0, v*env))
        f.writeframesraw(struct.pack('<h', int(v*amp)))
    f.close()

# Generate navigation ting with SLIGHTLY LESS resonance (decay 18.0 instead of 12.0)
mk('ting.wav', 0.12, 523.25, 659.25, 18.0, 24000.0, 0.01)
