from Box2D import *
import pyglet
from pyglet.gl import *
import rabbyt

from math import *
from operator import attrgetter
import random
import sys

def create_circle_vertex_list(center=(0., 0.), radius=1., vertex_count=100):
    x, y = center
    coords = []
    for i in xrange(vertex_count):
        angle = 2. * pi * float(i) / float(vertex_count)
        coords.append(x + radius * cos(angle))
        coords.append(y + radius * sin(angle))
        if i:
            coords.extend(coords[-2:])
    coords.extend(coords[:2])
    return pyglet.graphics.vertex_list(len(coords) // 2, ('v2f', coords))

def debug_draw(world):
    circle_vertex_list = create_circle_vertex_list()
    for body in world.bodyList:
        glPushMatrix()
        x, y = body.position.tuple()
        glTranslatef(x, y, 0.)
        glRotatef(rad_to_deg(body.angle), 0., 0., 1.)
        for shape in body.shapeList:
            if isinstance(shape, b2CircleShape):
                glPushMatrix()
                x, y = shape.localPosition.tuple()
                glTranslatef(x, y, 0.)
                glScalef(shape.radius, shape.radius, shape.radius)
                circle_vertex_list.draw(GL_LINES)
                glPopMatrix()
        glPopMatrix()

def rad_to_deg(angle):
    return angle * 180. / pi

def create_shadow(sprite, texture, x=20, y=-20):
    """Create a shadow sprite."""
    return MySprite(texture, scale=sprite.scale, alpha=0.8,
                    rot=(sprite.attrgetter('rot')),
                    x=(sprite.attrgetter('x') + x),
                    y=(sprite.attrgetter('y') + y),
                    z=(sprite.attrgetter('z') - 0.1))

def create_ao(sprite, texture):
    """Create an ambient occlusion (AO) sprite."""
    return create_shadow(sprite, texture, x=0, y=0)

class MySprite(rabbyt.Sprite):
    z = rabbyt.anim_slot()

def create_aabb(lower_bound, upper_bound):
    aabb = b2AABB()
    aabb.lowerBound = lower_bound
    aabb.upperBound = upper_bound
    return aabb

def create_circle_body(world, position=(0., 0.), radius=1., density=1.):
    body_def = b2BodyDef()
    body_def.position = position
    body = world.CreateBody(body_def)
    shape_def = b2CircleDef()
    shape_def.radius = radius
    shape_def.density = density
    body.CreateShape(shape_def)
    body.SetMassFromShapes()
    return body

class Camera(object):
    def __init__(self):
        # Translation, in meters.
        self.position = 0., 0.

        # Minimum width and height of screen, in meters.
        self.scale = 30.

        # Rotation, in degrees.
        self.angle = 0.

class Level(object):
    dt = 1. / 60.

    def __init__(self, debug=False):
        self.debug = debug
        self.time = 0.
        
        # The controllers to call every step.
        self.controllers = []

        # The sprites to draw every frame.
        self.sprites = []

        self._init_world()
        self._init_circle_vertex_list()
        self.camera = Camera()

    def _init_world(self):
        aabb = create_aabb((-100., -100.), (100., 100.))
        self.world = b2World(aabb, (0., 0.), True)

    def _init_circle_vertex_list(self):
        self.circle_vertex_list = create_circle_vertex_list()

    def step(self):
        self.time += self.dt
        for controller in self.controllers:
            controller.step()
        self.world.Step(self.dt, 10, 10)

    def draw(self, width, height):
        glPushMatrix()
        glTranslatef(float(width // 2), float(height // 2), 0.)
        scale = float(min(width, height)) / self.camera.scale
        glScalef(scale, scale, scale)
        for controller in self.controllers:
            controller.draw()
        rabbyt.set_time(self.time)
        self.sprites.sort(key=attrgetter('z'))
        rabbyt.render_unsorted(self.sprites)
        if self.debug:
            glColor3f(0., 1., 0.)
            glDisable(GL_TEXTURE_2D)
            debug_draw(self.world)
        glPopMatrix()

class Controller(object):
    def create(self):
        pass

    def delete(self):
        pass

class Challenge(Controller):
    """A challenge that the player encounters and must endure or overcome."""
    pass

class AsteroidField(Challenge):
    """The player must navigate through an asteroid field."""

    def __init__(self, screen):
        self.screen = screen
        self.asteroid_count = 0
        for _ in xrange(100):
            self.create_asteroid()

    def step(self, dt):
        pass

    def close(self):
        pass

    def create_asteroid(self):
        self.asteroid_count += 1
        angle = 2 * pi * random.random()
        distance = 1000
        x = self.screen.ship.x + distance * cos(angle)
        y = self.screen.ship.y + distance * sin(angle)
        scale = random.gauss(0.5, 0.1)
        asteroid = MySprite('asteroid.png', scale=scale, x=x, y=y)
        asteroid.x = rabbyt.lerp(end=(asteroid.x + 200 *
                                 (random.random() - 0.5)),
                                 dt=1, extend='extrapolate')
        asteroid.y = rabbyt.lerp(end=(asteroid.y + 200 *
                                 (random.random() - 0.5)),
                                 dt=1, extend='extrapolate')
        asteroid.z = -self.asteroid_count
        asteroid.rot = 360 * random.random()
        asteroid.rot = rabbyt.lerp(end=(asteroid.rot + 60 *
                                        (random.random() - 0.5)),
                                   dt=1, extend='extrapolate')
        asteroid.red = random.gauss(0.8, 0.2)
        asteroid.green = random.gauss(0.8, 0.2)
        asteroid.blue = random.gauss(0.8, 0.2)
        asteroid_ao = create_ao(asteroid, 'asteroid-shadow.png')
        asteroid_shadow = create_shadow(asteroid, 'asteroid-shadow.png')
        self.screen.collision_sprites.append(asteroid)
        self.screen.draw_sprites.extend([asteroid, asteroid_ao,
                                         asteroid_shadow])

class Battery(Controller):
    def __init__(self, ship):
        self.ship = ship

class LaserBattery(Battery):
    pass

class MissileBattery(Battery):
    pass

class Cannon(Controller):
    pass

class LaserCannon(Cannon):
    pass

class MissileRamp(Cannon):
    pass

class Shot(Controller):
    pass

class LaserBeam(Shot):
    pass

class Missile(Shot):
    pass

class Ship(Controller):
    thrust_force = 1000.
    damping = 20.

    def __init__(self, level):
        self.level = level
        self.keys = set()
        self.thrust = b2Vec2(0., 0.)
        self.batteries = [LaserBattery(self)]
        self.battery_index = 0
        self._init_body()
        self._init_sprite()
        self.level.controllers.append(self)

    def delete(self):
        self.level.controllers.remove(self)
        self.level.sprites.remove(self.sprite)
        self.level.world.DestroyBody(self.body)

    def _init_body(self):
        self.body = create_circle_body(self.level.world)
        self.body.userData = self

    def _init_sprite(self):
        self.sprite = MySprite('ship.png', scale=0.015)
        self.level.sprites.append(self.sprite)

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)

    def step(self):
        left = float(pyglet.window.key.LEFT in self.keys)
        right = float(pyglet.window.key.RIGHT in self.keys)
        up = float(pyglet.window.key.UP in self.keys)
        down = float(pyglet.window.key.DOWN in self.keys)

        self.thrust = b2Vec2(right - left, up - down)
        self.thrust.Normalize()
        force = (self.thrust * self.thrust_force -
                 self.body.GetLinearVelocity() * self.damping)
        self.body.ApplyForce(force, self.body.GetWorldCenter())

    def draw(self):
        self.sprite.xy = self.body.position.tuple()

class Asteroid(Controller):
    def __init__(self, level):
        self.level = level
        self._init_body()

    def _init_body(self):
        self.body = create_circle_body(self.level.world)
        self.body.userData = self

class GameScreen(object):
    def __init__(self, window, debug):
        self.window = window
        self.level = Level(debug)
        self.ship = Ship(self.level)
        self.time = 0.
        pyglet.clock.schedule_interval(self.step, self.level.dt)

    def step(self, dt):
        self.time += dt
        while self.level.time + self.level.dt < self.time:
            self.level.step()

    def on_draw(self):
        self.window.clear()
        self.level.draw(self.window.width, self.window.height)

    def close(self):
        pyglet.clock.unschedule(self.step)

    def on_key_press(self, symbol, modifiers):
        self.ship.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.ship.on_key_release(symbol, modifiers)
            
class MyWindow(pyglet.window.Window):
    def __init__(self, fps=False, debug=False, **kwargs):
        super(MyWindow, self).__init__(**kwargs)

        # Grab mouse and keyboard if we're in fullscreen mode.
        self.set_exclusive_mouse(self.fullscreen)
        self.set_exclusive_keyboard(self.fullscreen)

        # Initialize Rabbyt.
        rabbyt.set_default_attribs()

        # Clear to opaque black for opaque screenshots.
        glClearColor(0., 0., 0., 1.)

        # Create FPS display.
        self.fps_display = pyglet.clock.ClockDisplay() if fps else None

        # Most window calls are delegated to a screen.
        self.my_screen = GameScreen(self, debug)

    def on_draw(self):
        # Delegate to screen.
        self.my_screen.on_draw()

        # Display FPS counter.
        if self.fps_display is not None:
            self.fps_display.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            # Close window.
            self.on_close()
        elif symbol == pyglet.window.key.F11:
            # Toggle fullscreen mode.
            self.set_fullscreen(not self.fullscreen)
            self.set_exclusive_mouse(self.fullscreen)
            self.set_exclusive_keyboard(self.fullscreen)
        elif symbol == pyglet.window.key.F12:
            # Save screenshot.
            color_buffer = pyglet.image.get_buffer_manager().get_color_buffer()
            color_buffer.save('burst-screenshot.png')
        else:
            # Delegate to screen.
            self.my_screen.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        # Delegate to screen.
        self.my_screen.on_key_release(symbol, modifiers)

def help():
    print """
Usage: burst [OPTION]...

Options:
  --debug       Draw debug graphics.
  --fps         Display FPS counter.
  --fullscreen  Run in fullscreen mode (default).
  -h, --help    Print this helpful text and exit.
  --test        Run tests and exit.
  --windowed    Run in windowed mode.
""".strip()

def test():
    import doctest
    doctest.testmod()

def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        return help()
    if '--test' in args:
        return test()
    debug = '--debug' in args
    fps = '--fps' in args
    fullscreen = True
    for arg in args:
        if arg == '--fullscreen':
            fullscreen = True
        if arg == '--windowed':
            fullscreen = False
    window = MyWindow(debug=debug, fps=fps, fullscreen=fullscreen)
    pyglet.app.run()

if __name__ == '__main__':
    main()
