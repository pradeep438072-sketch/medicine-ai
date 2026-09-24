import os
import wave
import struct
import math

def generate_chime(filename="reminder.wav"):
    sample_rate = 44100
    duration = 1.2  # seconds
    num_samples = int(sample_rate * duration)
    
    # Dual chord chime: 523.25 Hz (C5) and 659.25 Hz (E5) and 783.99 Hz (G5) - Pleasant C Major chime
    frequencies = [523.25, 659.25, 783.99, 1046.50]
    
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Exponential decay envelope for gentle bell chime
            decay = math.exp(-3.5 * t)
            
            sample = 0.0
            for idx, freq in enumerate(frequencies):
                weight = 1.0 / (idx + 1)
                sample += weight * math.sin(2.0 * math.pi * freq * t)
            
            sample *= decay * 18000.0
            sample = max(-32767, min(32767, int(sample)))
            wav.writeframes(struct.pack('<h', sample))

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    wav_path = os.path.join(out_dir, "reminder.wav")
    generate_chime(wav_path)
    # Also write a copy as reminder.mp3 so both formats are covered
    with open(wav_path, "rb") as f_in, open(os.path.join(out_dir, "reminder.mp3"), "wb") as f_out:
        f_out.write(f_in.read())
    print("Generated sound file successfully.")
