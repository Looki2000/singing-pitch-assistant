import crepe
import pyaudio
import numpy as np
import threading
import pygame
#import matplotlib.pyplot as plt

# initialize pyaudio
p = pyaudio.PyAudio()


buffer_size = 256

# open stream
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=16000, input=True, frames_per_buffer=buffer_size)


# init pygame
pygame.init()
window_size = (1280, 720)
window = pygame.display.set_mode(window_size)
pygame.display.set_caption("Pitch Detection")

# create a clock
clock = pygame.time.Clock()


#detecting = False
#
#def pitch_detection():
#    global detecting
#
#    # predict
#    time, frequency, confidence, activation = crepe.predict(audio, 16000, model_capacity="tiny", verbose=0)
#
#    ## print the result
#    #if confidence > 0.6:
#    #    print(frequency)
#    #else:
#    #    print("---")
#
#    print(frequency, confidence)
#    detecting = False
#
#
#while True:
#    # read data
#    data = stream.read(1024)
#    audio = np.frombuffer(data, dtype=np.int16)
#
#    # create thread
#    while detecting:
#        pass
#    
#    detecting = True
#    t = threading.Thread(target=pitch_detection, daemon=True)
#    t.start()



new_audio = False
audio = None

def read_audio():
    global audio
    global new_audio

    while True:
        data = stream.read(buffer_size)
        audio = np.frombuffer(data, dtype=np.float32)
        new_audio = True
        #print("new audio")






t = threading.Thread(target=read_audio, daemon=True)
t.start()

#plt.ion()

#fig = plt.figure()
#ax = fig.add_subplot(111)
#wave_line, = ax.plot(np.zeros(1024))


step_size = int(buffer_size / 16000 * 1000)
#print(step_size)

current_freq = 0

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
        

        # predict
        time, frequency, confidence, activation = crepe.predict(audio, 16000, model_capacity="tiny", center=False, step_size=step_size, verbose=0)

        ## print the result
        #if confidence > 0.6:
        #    print(frequency)
        #else:
        #    print("---")

        print(frequency, confidence)
        
        window.fill((0, 0, 0))

        if confidence[0] > 0.1:
            current_freq = frequency[0]
            color = (150, 255, 150)
        else:
            color = (255, 200, 150)

        pygame.draw.circle(window, color, (100, int(current_freq)), 10)

        new_audio = False


    # update the window
    pygame.display.update()
    #clock.tick(60)

