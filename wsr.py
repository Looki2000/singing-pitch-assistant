import numpy as np
import pygame

class Dirs:
    left = 0
    right = 1
    up = 2
    down = 3

class Axis:
    x = 0
    y = 1
    xy = 2



class Object:
    rect = 0
    line = 1
    curve = 2

class WSR:
    def __init__(self, pg_window, init_view_pos=(0, 0), init_view_zoom=(1, 1), debug=False):
        self.window = pg_window
        self.view_pos = np.array(init_view_pos, dtype=np.float32)
        self.view_zoom = np.array(init_view_zoom, dtype=np.float32)
        self.debug = debug
        
        self.objects = []
        self.need_sort = False

    def get_window_size(self):
        return np.array(self.window.get_size())

    def add_rect(self, color, pos, size, thick=None, z_index=0, stick=None, screen_space_lock_axis=None, hidden=False):
        pos = np.array(pos, dtype=np.float32)
        size = np.array(size, dtype=np.float32)

        for i in range(2):
            if size[i] < 0:
                pos[i] += size[i]
                size[i] *= -1

        if self.debug:
            print(f"add rect | color {color} | pos {pos} | size {size}")

        self.objects.append(
            [
                Object.rect, 
                [color, pos, size, thick], 
                z_index,
                stick,
                screen_space_lock_axis,
                hidden
            ]
        )

        self.need_sort = True
    
    def add_rect_corners(self, color, pos1, pos2, thick=None, z_index=0, stick=None, screen_space_lock_axis=None, hidden=False):
        pos1 = np.array(pos1, dtype=np.float32)
        pos2 = np.array(pos2, dtype=np.float32)
        self.add_rect(color, pos1, pos2 - pos1, thick, z_index, stick, screen_space_lock_axis, hidden)

    def add_line(self, color, pos1, pos2, thick=1, z_index=0, stick=None, screen_space_lock_axis=None, hidden=False):
        pos1 = np.array(pos1, dtype=np.float32)
        pos2 = np.array(pos2, dtype=np.float32)

        self.objects.append(
            [
                Object.line, 
                [color, pos1, pos2, thick],
                z_index,
                stick,
                screen_space_lock_axis,
                hidden
            ]
        )

        self.need_sort = True

        return self.objects[-1]

    def add_line_delta(self, color, pos, pos_delta, thick=1, z_index=0, stick=None, screen_space_lock_axis=None, hidden=False):
        pos = np.array(pos, dtype=np.float32)
        pos_delta = np.array(pos_delta, dtype=np.float32)

        self.add_line(color, pos, pos + pos_delta, thick, z_index, stick, screen_space_lock_axis, hidden)

    def add_curve(self, color, y_points, width, y_color_coeff=None, coeff_tresh=None, color_secondary=(0,0,0), thick=1, z_index=0):
        y_points = np.array(y_points, dtype=np.float32)

        # Generate the indices for the original array
        x_old = np.linspace(0, 1, len(y_points))

        if y_color_coeff is not None and len(y_points) != len(y_color_coeff):
            raise ValueError("y_points and y_color_coeff must have the same length!")


        self.objects.append(
            [
                Object.curve,
                [color, y_points, width, y_color_coeff, coeff_tresh, color_secondary, thick, x_old],
                z_index
            ]
        )

        self.need_sort = True

        return self.objects[-1]

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


        if self.need_sort:
            self.objects = sorted(self.objects, key=lambda x: x[2])
            self.need_sort = False


        #for obj in sorted(self.objects, key=lambda x: x[2]):
        for i, obj in enumerate(self.objects):
            if obj[0] == Object.rect:
                if obj[5]:
                    continue

                color, pos, size, thick = obj[1]
                pos, size = pos.copy(), size.copy()
                pos = pos * self.view_zoom + self.view_pos


                if obj[4] is not None:
                    if obj[4] == Axis.x:
                        size[1] *= self.view_zoom[1]
                    elif obj[4] == Axis.y:
                        size[0] *= self.view_zoom[0]
                    # Axis.xy keeps everything the same
                else:
                    size *= self.view_zoom


                if obj[3] is not None:
                    if obj[3] == Dirs.left:
                        pos[0] = 0
                    elif obj[3] == Dirs.right:
                        pos[0] = win_size[0] - size[0]
                    elif obj[3] == Dirs.up:
                        pos[1] = 0
                    elif obj[3] == Dirs.down:
                        pos[1] = win_size[1] - size[1]

                pos = pos.astype(int)
                size = size.astype(int)



                if thick is None:
                    pygame.draw.rect(self.window, color, (*pos, *size))
                else:
                    #print((*pos, *size))
                    pygame.draw.rect(self.window, color, (*pos, *size), thick)


            elif obj[0] == Object.line:
                if obj[5]:
                    continue

                if obj[3] is not None:
                    raise ValueError("stick not yet implemented for lines")
                if obj[4] is not None:
                    raise ValueError("screen_space_lock_axis not yet implemented for lines")

                color, pos1, pos2, thick = obj[1]

                pos1 = pos1 * self.view_zoom + self.view_pos
                pos2 = pos2 * self.view_zoom + self.view_pos

                pos1 = pos1.astype(int)
                pos2 = pos2.astype(int)

                pygame.draw.line(self.window, color, pos1, pos2, thick)

            elif obj[0] == Object.curve:
                color, y_points, width, y_color_coeff, coeff_tresh, color_secondary, thick, x_old = obj[1]

                # let's assume start point of curve is 0.0 and end is 1.0
                # we need to calculate what range from 0.0 to 1.0 is visible on screen
                
                left_range = -self.view_pos[0] / self.view_zoom[0] / width
                right_range = (win_size[0] - self.view_pos[0]) / self.view_zoom[0] / width

                #print(left_range, right_range)

                x_new = np.linspace(left_range, right_range, win_size[0])

                y_new = np.interp(x_new, x_old, y_points)

                if y_color_coeff is not None and coeff_tresh is None:
                    color_new = np.interp(x_new, x_old, y_color_coeff)
                    # expand to 3 channels
                    color_new = np.expand_dims(color_new, axis=1)
                    color_new = np.repeat(color_new, 3, axis=1)

                    color_new = color_new * color + (1 - color_new) * color_secondary

                    color_new = color_new.astype(int)

                elif coeff_tresh is not None:
                    coeff_new = np.interp(x_new, x_old, y_color_coeff)

                    coeff_new = coeff_new > coeff_tresh
                
                
                y_new = y_new * self.view_zoom[1] + self.view_pos[1]

                y_new = y_new.astype(int)

                for i in range(1, len(y_new)):
                    if coeff_tresh is not None and not coeff_new[i]:
                        continue
                    a = (i - 1, y_new[i - 1])
                    b = (i, y_new[i])
                    col = tuple(color_new[i]) if (y_color_coeff is not None and coeff_tresh is None) else color
                    pygame.draw.line(self.window, col, a, b, thick)



if __name__ == "__main__":
    window_size = (1280, 720)
    fps_limit = 240

    pygame.init()
    window = pygame.display.set_mode(window_size)
    clock = pygame.time.Clock()

    wsr = WSR(window)

    wsr.add_rect((255, 0, 0), (100, 100), (100, 100), stick=Dirs.left, screen_space_lock_axis=Axis.x)
    wsr.add_rect((0, 255, 0), (200, 200), (100, 100))
    wsr.add_line((0, 0, 255), (300, 300), (400, 400))

    wsr.add_rect((255, 255, 255), np.array([0, 0]), window_size, thick=3, z_index=-1)

    for i in range(0):
        wsr.add_rect(
            np.random.randint(0, 255, 3),
            np.random.randint(0, window_size),
            np.random.randint(10, 100, 2),
            z_index = -2
        )


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