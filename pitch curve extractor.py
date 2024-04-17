import torchcrepe
import numpy as np
import torch
import soundfile as sf
#import matplotlib.pyplot as plt
import os
import pickle

cwd = os.path.dirname(os.path.realpath(__file__))

audio_path = input("audio path or drag and drop > ")
bpm = input("bpm > ")

# if bpm is whole number convert to int. Otherwise convert to float
if bpm.isnumeric():
    bpm = int(bpm)
    print("bpm is int")
else:
    bpm = float(bpm)
    print("bpm is float")


audio, sample_rate = sf.read(audio_path)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# mix to mono if needed
if audio.ndim > 1:
    audio = np.mean(audio, axis=1)

audio = torch.tensor([audio], dtype=torch.float32).to(device)


hop_length = int(sample_rate / 200.)

fmin = 50
fmax = 550

model = "full"



batch_size = 2048


pitch, confidence = torchcrepe.predict(
    audio,
    sample_rate,
    hop_length,
    fmin,
    fmax,
    model,
    return_periodicity=True,
    batch_size=batch_size,
    device=device
)

pitch = pitch.cpu().numpy()[0]
confidence = confidence.cpu().numpy()[0]

#print(pitch, confidence)
#print(pitch.shape, confidence.shape)
#
## plot pitch curve and confidence
#plt.figure()
#plt.plot(pitch)
#plt.plot(confidence*500)
#
#plt.show()



# split path from file name
path, file = os.path.split(audio_path)

# get file name without extension
file = os.path.splitext(file)[0]

# create new path
new_path = os.path.join(cwd, "extracted_pitch")

# create new folder if it doesn't exist
if not os.path.exists(new_path):
    os.makedirs(new_path)

new_path = os.path.join(new_path, file + "_pitch_curve.pkl")


# calculate and print song length in minutes
test = len(pitch) / (sample_rate / hop_length)
print(test, test / 60)

# calculate and print song length in samples
test2 = len(pitch) / hop_length

print(len(pitch), sample_rate, hop_length)


# save pitch curve and confidence
with open(new_path, "wb") as f:
    #pickle.dump((pitch, confidence, sample_rate, hop_length), f)
    pickle.dump((pitch, confidence, len(audio[0]), bpm, sample_rate), f)