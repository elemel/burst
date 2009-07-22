from math import *
import pyglet
from pyglet.gl import *
import rabbyt
import random
import sys

TIME_STEP = 1. / 60.

class Challenge(object):
    pass

class AsteroidField(Challenge):
    def __init__(self, screen):
        self.screen = screen
        self.asteroids = []
        for _ in xrange(50):
            self.create_asteroid()

    def on_draw(self):
        rabbyt.render_unsorted(self.asteroids)

    def step(self, dt):
        pass

    def close(self):
        pass

    def create_asteroid(self):
        angle = 2 * pi * random.random()
        distance = 1000
        x = self.screen.ship.x + distance * cos(angle)
        y = self.screen.ship.y + distance * sin(angle)
        scale = random.gauss(0.4, 0.05)
        asteroid = rabbyt.Sprite('asteroid.png', scale=scale, x=x, y=y)
        asteroid.x = rabbyt.lerp(end=(asteroid.x + 200 *
                                 (random.random() - 0.5)),
                                 dt=1, extend='extrapolate')
        asteroid.y = rabbyt.lerp(end=(asteroid.y + 200 *
                                 (random.random() - 0.5)),
                                 dt=1, extend='extrapolate')
        asteroid.rot = 360 * random.random()
        asteroid.rot = rabbyt.lerp(end=(asteroid.rot + 60 *
                                        (random.random() - 0.5)),
                                   dt=1, extend='extrapolate')
        asteroid.red = random.gauss(0.8, 0.2)
        asteroid.green = random.gauss(0.8, 0.2)
        asteroid.blue = random.gauss(0.8, 0.2)
        self.asteroids.append(asteroid)

class ShipControls(object):
    def __init__(self, screen, ship):
        self.screen = screen
        self.ship = ship
        self.keys = set()
        self.speed = 400
        self.cooldown = 0.1
        self.fire_time = -60
        self.shot_speed = 600
        self.shot_x = 0
        self.shot_y = 30
        self.shot_x_sigma = 5
        self.shot_y_sigma = 1
        self.shot_rot_sigma = 1
        self.shield_time = 0.3

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
        self.ship.x = rabbyt.lerp(end=(self.ship.x + dx), dt=1,
                                  extend='extrapolate')
        self.ship.y = rabbyt.lerp(end=(self.ship.y + dy), dt=1,
                                  extend='extrapolate')

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)
        self.update_speed()

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)
        self.update_speed()

class GameScreen(object):
    def __init__(self, window):
        self.window = window
        self.ship = rabbyt.Sprite('ship.png', scale=0.35)
        self.shield = rabbyt.Sprite('shield.png', scale=0.3)
        self.shield.xy = self.ship.attrgetter('xy')
        self.shield.rot = rabbyt.lerp(end=10, dt=1, extend='extrapolate')
        self.controls = ShipControls(self, self.ship)
        self.shots = []
        self.challenge = AsteroidField(self)
        self.time = 0.
        pyglet.clock.schedule_interval(self.step, TIME_STEP)

    def step(self, dt):
        self.time += dt
        self.controls.step(dt)
        self.challenge.step(dt)
        rabbyt.set_time(self.time)

    def on_draw(self):
        rabbyt.set_default_attribs()
        rabbyt.clear()
        glPushMatrix()
        glTranslatef(self.window.width // 2, self.window.height // 2, 0)
        self.challenge.on_draw()
        rabbyt.render_unsorted(self.shots)
        rabbyt.render_unsorted([self.ship])
        if (self.controls.fire_time + self.controls.shield_time
            < rabbyt.get_time()):
            rabbyt.render_unsorted([self.shield])
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
