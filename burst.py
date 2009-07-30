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

def create_circle_body(world, position=(0., 0.), linear_velocity=(0., 0.),
                       angle=0., radius=1., density=1., group_index=0):
    body_def = b2BodyDef()
    body_def.position = position
    body_def.angle = angle
    body = world.CreateBody(body_def)
    shape_def = b2CircleDef()
    shape_def.radius = radius
    shape_def.density = density
    shape_def.filter.groupIndex = group_index
    body.CreateShape(shape_def)
    body.SetMassFromShapes()
    body.linearVelocity = linear_velocity
    return body

def create_prismatic_joint(world, body_1, body_2, anchor=None, axis=None,
                           lower_translation=-1., upper_translation=1.,
                           max_motor_force=1., motor_speed=1.):
    if anchor is None:
        anchor = body_2.position
    if axis is None:
        axis = body_1.GetWorldVector(b2Vec2(0., 1.))
    joint_def = b2PrismaticJointDef()
    joint_def.Initialize(body_1, body_2, anchor, axis)
    joint_def.enableLimit = True
    joint_def.lowerTranslation = lower_translation
    joint_def.upperTranslation = upper_translation
    joint_def.enableMotor = True
    joint_def.maxMotorForce = max_motor_force
    joint_def.motorSpeed = motor_speed
    world.CreateJoint(joint_def)

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
        
        # Things coordinate bodies and sprites.
        self.things = []

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
        for thing in self.things:
            thing.step()
        self.world.Step(self.dt, 10, 10)

    def draw(self, width, height):
        glPushMatrix()
        glTranslatef(float(width // 2), float(height // 2), 0.)
        scale = float(min(width, height)) / self.camera.scale
        glScalef(scale, scale, scale)
        rabbyt.set_time(self.time)
        self.sprites.sort(key=attrgetter('z'))
        rabbyt.render_unsorted(self.sprites)
        if self.debug:
            glColor3f(0., 1., 0.)
            glDisable(GL_TEXTURE_2D)
            debug_draw(self.world)
        glPopMatrix()

class Thing(object):
    """A physical, visible thing.

    Things have a circular physics body and a sprite that moves and rotates
    with the body.

    For non-physical stuff, such as pure special effects, use sprites directly
    instead.
    """

    radius = 1.
    density = 1.
    group_index = 0
    texture = None
    scale = 1.
    fade_dt = 0.5

    def __init__(self, level, position=(0., 0.), linear_velocity=(0., 0.),
                 angle=0., z=0.):
        self.level = level
        self._init_body(position=position, linear_velocity=linear_velocity,
                        angle=angle)
        self._init_sprite(z=z)
        self.level.things.append(self)

    def _init_body(self, position=(0., 0.), linear_velocity=(0., 0.),
                   angle=0.):
        self.body = create_circle_body(self.level.world,
                                       position=position,
                                       linear_velocity=linear_velocity,
                                       angle=angle,
                                       radius=self.radius,
                                       density=self.density,
                                       group_index=self.group_index)
        self.body.userData = self

    def _init_sprite(self, z=0.):
        self.sprite = MySprite(texture=self.texture, scale=self.scale,
                               alpha=0., z=z)
        self.level.sprites.append(self.sprite)

        self.sprite.x = lambda: self.body.position.x
        self.sprite.y = lambda: self.body.position.y
        self.sprite.rot = lambda: rad_to_deg(self.body.angle)

        self.fade_in()

    def delete(self):
        self.level.things.remove(self)
        self.level.sprites.remove(self.sprite)
        self.level.world.DestroyBody(self.body)

    def step(self):
        pass

    def fade_in(self):
        dt = self.fade_dt * (1. - self.sprite.alpha)
        self.sprite.alpha = rabbyt.lerp(end=1., dt=dt)

    def fade_out(self):
        dt = self.fade_dt * self.sprite.alpha
        self.sprite.alpha = rabbyt.lerp(end=0., dt=self.fade_dt)

class Challenge(object):
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

class Cannon(Thing):
    radius = 0.1

    def __init__(self, ship, **kwargs):
        super(Cannon, self).__init__(**kwargs)
        self.ship = ship
        self.firing = False
        self.fire_time = self.level.time

class PlasmaCannon(Cannon):
    texture = 'plasma-cannon.png'
    scale = 0.015
    group_index = -1
    recoil = 1.5
    cooldown_mean = 0.3
    cooldown_dev = 0.05
    muzzle_velocity = 50.

    def __init__(self, **kwargs):
        super(PlasmaCannon, self).__init__(**kwargs)
        self.cooldown = random.gauss(self.cooldown_mean, self.cooldown_dev)

    def step(self):
        if self.firing and self.fire_time + self.cooldown < self.level.time:
            # Spread the cooldown, so that the cannons are only synchronized
            # for the very first shots after a cease fire.
            self.fire_time = self.level.time
            self.cooldown = random.gauss(self.cooldown_mean, self.cooldown_dev)
            self.fire()

    def fire(self):
        # Don't add the ship's linear velocity to the shot's linear velocity.
        # If the ship is moving sideways, the shots would also move sideways.
        # It doesn't look good, and it doesn't feel good either. Space Invaders
        # was right.
        #
        # TODO: However, we may want to add the linear velocity component in
        # the cannon's direction, or adjust the linear velocity for scrolling.
        muzzle_velocity = b2Vec2(0., self.muzzle_velocity)
        linear_velocity = self.body.GetWorldVector(muzzle_velocity)
        shot = PlasmaShot(level=self.level, position=self.body.position,
                          linear_velocity=linear_velocity,
                          angle=self.body.angle)
        recoil = self.recoil * self.body.GetWorldVector(b2Vec2(0., -1.))
        self.body.ApplyImpulse(recoil, self.body.position)

class MissileRamp(Cannon):
    pass

class Shot(Thing):
    fade_dt = 0.1

class PlasmaShot(Shot):
    texture = 'plasma-shot.png'
    scale = 0.015
    group_index = -1
    radius = 0.1

class Missile(Shot):
    pass

class Ship(Thing):
    thrust_force = 700.
    damping_force = 20.
    turn_torque = 500.
    damping_torque = 20.
    cannon_slots = [(-0.75, 0.75), (0., 1.5), (0.75, 0.75)]
    group_index = -1
    texture = 'ship.png'
    scale = 0.015

    def __init__(self, **kwargs):
        super(Ship, self).__init__(**kwargs)
        self.locking = False
        self.thrust = b2Vec2(0., 0.)
        self.cannons = [None, None, None]
        for i in xrange(3):
            position = self.body.GetWorldPoint(self.cannon_slots[i])
            z = self.sprite.attrgetter('z') - 0.1
            self.cannons[i] = PlasmaCannon(level=self.level, ship=self,
                                           position=position,
                                           angle=self.body.angle, z=z)
            create_prismatic_joint(self.level.world, self.body,
                                   self.cannons[i].body, upper_translation=0.,
                                   max_motor_force=20., motor_speed=5.)
            self.angle = self.body.angle
        self.linear_velocity = b2Vec2(0., 0.)

    # TODO: Set self.linear_velocity from e.g. scrolling.
    #
    # TODO: Set self.angle from e.g. locking or scrolling.
    def step(self):
        self._apply_force()
        self._apply_torque()

    def _apply_force(self):
        linear_velocity_error = self.linear_velocity - self.body.linearVelocity
        force = (self.thrust * self.thrust_force +
                 linear_velocity_error * self.damping_force)
        self.body.ApplyForce(force, self.body.position)

    def _apply_torque(self):
        torque = (self.turn_torque * (self.angle - self.body.angle) -
                  self.damping_torque * self.body.angularVelocity)
        self.body.ApplyTorque(torque)

class ShipControls(object):
    def __init__(self, level, ship):
        self.level = level
        self.ship = ship
        self.keys = set()

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)
        self.update()

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)
        self.update()

    def update(self):
        self._update_thrust()
        self._update_firing()
        self.ship.locking = pyglet.window.key.ENTER in self.keys

    def _update_thrust(self):
        left = float(pyglet.window.key.LEFT in self.keys)
        right = float(pyglet.window.key.RIGHT in self.keys)
        up = float(pyglet.window.key.UP in self.keys)
        down = float(pyglet.window.key.DOWN in self.keys)

        thrust = b2Vec2(right - left, up - down)
        thrust.Normalize()
        self.ship.thrust = thrust

    def _update_firing(self):
        for cannon in self.ship.cannons:
            cannon.firing = pyglet.window.key.SPACE in self.keys

class Asteroid(Thing):
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
        self.ship = Ship(level=self.level)
        self.controls = ShipControls(self.level, self.ship)
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
        self.controls.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.controls.on_key_release(symbol, modifiers)
            
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
  -v            Enable verbose output (use with --test).
  --windowed    Run in windowed mode.

Controls:
  Arrows        Fly.
  Space         Fire.
  Enter         Toggle target locking.

  Escape        Exit.
  F11           Toggle fullscreen mode.
  F12           Save a screenshot.
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
