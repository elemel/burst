from math import *
import pyglet
from pyglet.gl import *
import rabbyt
import random
import sys

TIME_STEP = 1. / 60.

class ShipControls(object):
    def __init__(self, screen, ship):
        self.screen = screen
        self.ship = ship
        self.keys = set()
        self.speed = 400
        self.cooldown = 0.1
        self.fire_time = 0
        self.shot_speed = 600
        self.shot_x = -5
        self.shot_y = 30
        self.shot_x_sigma = 5
        self.shot_y_sigma = 1
        self.shot_rot_sigma = 1

    def step(self, dt):
        firing = pyglet.window.key.SPACE in self.keys
        if firing and rabbyt.get_time() > self.fire_time + self.cooldown:
            self.fire()

    def fire(self):
        self.fire_time = rabbyt.get_time()
        shot = rabbyt.Sprite('laser.png', scale=0.35)
        shot.x = random.gauss(self.ship.x + self.shot_x, self.shot_x_sigma)
        shot.y = random.gauss(self.ship.y + self.shot_y, self.shot_y_sigma)
        shot.rot = random.gauss(self.ship.rot, self.shot_rot_sigma)
        dy = self.shot_speed * cos(shot.rot * pi / 180)
        dx = self.shot_speed * -sin(shot.rot * pi / 180)
        shot.x = rabbyt.lerp(end=(shot.x + dx), dt=1.0, extend='extrapolate')
        shot.y = rabbyt.lerp(end=(shot.y + dy), dt=1.0, extend='extrapolate')
        self.screen.shots.append(shot)

    def update_speed(self):
        left = pyglet.window.key.LEFT in self.keys
        right = pyglet.window.key.RIGHT in self.keys
        up = pyglet.window.key.UP in self.keys
        down = pyglet.window.key.DOWN in self.keys

        dx = self.speed * (int(right) - int(left))
        dy = self.speed * (int(up) - int(down))
        self.ship.rot = 10 * (int(left) - int(right))
        self.ship.x = rabbyt.lerp(end=(self.ship.x + dx), dt=1.0,
                                  extend='extrapolate')
        self.ship.y = rabbyt.lerp(end=(self.ship.y + dy), dt=1.0,
                                  extend='extrapolate')

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)
        self.update_speed()

    def on_key_release(self, symbol, modifiers):
        self.keys.remove(symbol)
        self.update_speed()

class GameScreen(object):
    def __init__(self, window):
        self.window = window
        self.ship = rabbyt.Sprite('ship.png', scale=0.35)
        self.controls = ShipControls(self, self.ship)
        self.shots = []
        self.time = 0.
        pyglet.clock.schedule_interval(self.step, TIME_STEP)

    def step(self, dt):
        self.time += dt
        self.controls.step(dt)
        rabbyt.set_time(self.time)

    def on_draw(self):
        rabbyt.set_default_attribs()
        rabbyt.clear()
        glPushMatrix()
        glTranslatef(self.window.width // 2, self.window.height // 2, 0)
        rabbyt.render_unsorted(self.shots)
        rabbyt.render_unsorted([self.ship])
        glPopMatrix()

    def close(self):
        pyglet.clock.unschedule(self.step)

    def on_key_press(self, symbol, modifiers):
        self.controls.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.controls.on_key_release(symbol, modifiers)
            
class MyWindow(pyglet.window.Window):
    def __init__(self, **kwargs):
        super(MyWindow, self).__init__(**kwargs)
        if self.fullscreen:
            self.set_exclusive_mouse(True)
            self.set_exclusive_keyboard(True)
        self.my_screen = GameScreen(self)

    def on_draw(self):
        self.my_screen.on_draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close()
        else:
            self.my_screen.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.my_screen.on_key_release(symbol, modifiers)

def main():
    window = MyWindow(fullscreen=('--fullscreen' in sys.argv))
    pyglet.app.run()

if __name__ == '__main__':
    main()
