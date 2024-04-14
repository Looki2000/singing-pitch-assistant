import numpy as np
import pygame

class Dirs:
    left = 0
    right = 1
    up = 2
    down = 3

class Object:
    rect = 0
    line = 1

class Axis:
    x = 0
    y = 1

class WSR:
    def __init__(self, pg_window, init_view_pos=np.array([0, 0], dtype=np.float32), init_view_zoom=np.array([1, 1], dtype=np.float32)):
        self.window = pg_window
        self.view_pos = init_view_pos
        self.view_zoom = init_view_zoom
        
        self.objects = []

    def get_window_size(self):
        return np.array(self.window.get_size())

    def add_rect(self, color, pos, size, thick=None, z_index=0, stick=None):
        self.objects.append(
            [
                Object.rect, 
                [color, pos, size, thick], 
                z_index,
                stick
            ]
        )
    
    def add_rect_corners(self, color, pos1, pos2, thick=None, z_index=0, stick=None):
        self.add_rect(color, pos1, pos2 - pos1, thick, z_index, stick)

    def add_line(self, color, pos1, pos2, thick=1, z_index=0, stick=None):
        self.objects.append(
            [
                Object.line, 
                [color, pos1, pos2, thick],
                z_index,
                stick
            ]
        )

    def move_view_screen_space(self, delta):
        self.view_pos += delta

    def zoom_view(self, zoom, center, axis=None):
        if axis is None:
            self.view_zoom *= zoom
            self.view_pos += (center - self.view_pos) * (1 - zoom)
        else:
            self.view_zoom[axis] *= zoom
            self.view_pos[axis] += (center[axis] - self.view_pos[axis]) * (1 - zoom)


        

    def render(self):
        #print(self.view_pos, self.view_zoom)

        win_size = self.get_window_size()

        #print("rendering")

        for obj in sorted(self.objects, key=lambda x: x[2]):
            if obj[0] == Object.rect:
                #print("rect")
                color, pos, size, thick = obj[1]
                pos = pos * self.view_zoom + self.view_pos
                size = size * self.view_zoom

                if obj[3] is not None:
                    if obj[3] == Dirs.left:
                        pos[0] = 0
                    elif obj[3] == Dirs.right:
                        pos[0] = win_size[0] - size[0]
                    elif obj[3] == Dirs.up:
                        pos[1] = 0
                    elif obj[3] == Dirs.down:
                        pos[1] = win_size[1] - size[1]


                if thick is None:
                    pygame.draw.rect(self.window, color, (*pos, *size))
                else:
                    pygame.draw.rect(self.window, color, (*pos, *size), thick)

            elif obj[0] == Object.line:
                #print("line")
                color, pos1, pos2, thick = obj[1]
                pos1 = pos1 * self.view_zoom + self.view_pos
                pos2 = pos2 * self.view_zoom + self.view_pos

                pygame.draw.line(self.window, color, pos1, pos2, thick)



if __name__ == "__main__":
    window_size = (1280, 720)
    fps_limit = 240

    pygame.init()
    window = pygame.display.set_mode(window_size)
    clock = pygame.time.Clock()

    wsr = WSR(window)

    wsr.add_rect((255, 0, 0), np.array([100, 100]), np.array([100, 100]), stick=Dirs.left)
    wsr.add_rect((0, 255, 0), np.array([200, 200]), np.array([100, 100]))
    wsr.add_line((0, 0, 255), np.array([300, 300]), np.array([400, 400]))

    wsr.add_rect((255, 255, 255), np.array([0, 0]), window_size, thick=3, z_index=-1)

    while True:
        scroll_rel = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEWHEEL:
                scroll_rel = event.y


        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        mouse_pos = np.array(pygame.mouse.get_pos(), dtype=np.float32)
        mouse_rel = np.array(pygame.mouse.get_rel(), dtype=np.float32)


        # y zoom
        if keys[pygame.K_LCTRL] and mouse_buttons[1]:
            wsr.zoom_view(1 - mouse_rel[1] / 100, mouse_pos, Axis.y)
        
        # 2D movement
        elif mouse_buttons[1]:
                wsr.move_view_screen_space(mouse_rel)

        elif keys[pygame.K_LCTRL] and scroll_rel:
            wsr.zoom_view(1 + scroll_rel / 5, mouse_pos, axis=Axis.x)


        window.fill((0, 0, 0))

        wsr.render()

        pygame.display.update()
        clock.tick(fps_limit)