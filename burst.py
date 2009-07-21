import pyglet
import rabbyt
import sys

TIME_STEP = 1. / 60.

class GameScreen(object):
    def __init__(self, window):
        self.window = window
        self.sprites = [rabbyt.Sprite('ship.png')]
        self.time = 0.
        pyglet.clock.schedule_interval(self.step, TIME_STEP)

    def step(self, dt):
        self.time += dt
        rabbyt.set_time(self.time)

    def on_draw(self):
        rabbyt.render_unsorted(self.sprites)

    def close(self):
        pyglet.clock.unschedule(self.step)

class MyWindow(pyglet.window.Window):
    def __init__(self, **kwargs):
        super(MyWindow, self).__init__(**kwargs)
        if self.fullscreen:
            self.set_exclusive_mouse(True)
            self.set_exclusive_keyboard(True)
        self.my_screen = GameScreen(self)

    def on_draw(self):
        self.my_screen.on_draw()

def main():
    window = MyWindow(fullscreen=('--fullscreen' in sys.argv))
    pyglet.app.run()

if __name__ == '__main__':
    main()
