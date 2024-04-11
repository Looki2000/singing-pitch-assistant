import torchcrepe
import pyaudio
import numpy as np
import threading
import pygame
import torch
#import matplotlib.pyplot as plt

# initialize pyaudio
p = pyaudio.PyAudio()


buffer_size = 1024


bad_color = tuple((np.array([255, 200, 150]) * 0.25).astype(np.uint8))


# open stream
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=16000, input=True, frames_per_buffer=buffer_size)


# init pygame
pygame.init()
window_size = (1280, 720)
window = pygame.display.set_mode(window_size)
pygame.display.set_caption("Pitch Detection")

# create a clock
clock = pygame.time.Clock()



new_audio = False
audio = None

def read_audio():
    global audio
    global new_audio

    while True:
        data = stream.read(buffer_size)
        #audio = np.frombuffer(data, dtype=np.float32)

        # to tensor
        audio = torch.tensor([np.frombuffer(data, dtype=np.float32)])

        new_audio = True
        #print("new audio")






t = threading.Thread(target=read_audio, daemon=True)
t.start()

#plt.ion()

#fig = plt.figure()
#ax = fig.add_subplot(111)
#wave_line, = ax.plot(np.zeros(1024))


#step_size = int(buffer_size / 16000 * 1000)
#print(step_size)

current_freq = 0

pos_x = 0

while True:

    # check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            p.terminate()
            exit()


    if new_audio:

        # plot
        #wave_line.set_ydata(audio)
        #fig.canvas.draw()
        #fig.canvas.flush_events()
        
        #print(audio.dtype, audio.shape)
        #print(audio.size)

        # predict
        frequency, confidence = torchcrepe.predict(
            audio,
            sample_rate=16000,
            hop_length=buffer_size,
            model="tiny",
            batch_size=buffer_size,
            pad=False,
            return_periodicity=True,
        )

        ## print the result
        #if confidence > 0.6:
        #    print(frequency)
        #else:
        #    print("---")

        #print(frequency, confidence)
        #print(current_freq)
        
        #window.fill((0, 0, 0))

        if confidence[0] > 0.5:
            display_freq = frequency[0]
            
            # convert to mel scale
            #current_freq = 2595.0 * np.log10(1.0 + display_freq / 700.0)

            current_freq = np.log2((frequency-50) / 440 + 1)



            # scale
            current_freq = current_freq * 1000

            print(current_freq)

            # flip to display correctly
            current_freq = window_size[1] - current_freq



            color = (150, 255, 150)
        else:
            color = bad_color


        pygame.draw.circle(window, color, (pos_x, int(current_freq)), 5)
        pos_x += 10

        if pos_x >= window_size[0]:
            pos_x = 0
            window.fill((0, 0, 0))

        new_audio = False


    # update the window
        pygame.display.update()
    #clock.tick(60)

