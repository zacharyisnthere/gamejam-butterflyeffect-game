#!/home/zachary/Documents/Repos/pygame/butterfly-effect-gamejam/venv/bin/python

import pygame
import numpy as np
import random


#settings
default_buffer = 0

LEFT = [pygame.K_LEFT, pygame.K_a]
RIGHT = [pygame.K_RIGHT, pygame.K_d]
UP = [pygame.K_UP, pygame.K_w]
DOWN = [pygame.K_DOWN, pygame.K_s]

#constants
PLAY_WIDTH, PLAY_HEIGHT = 540, 540
WINDOW_WIDTH, WINDOW_HEIGHT = PLAY_WIDTH+default_buffer, PLAY_HEIGHT+default_buffer





def main(width, height, fps, starting_scene):
    pygame.init()
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    canvas = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT))
    canvas_rect = canvas.get_frect()
    clock = pygame.time.Clock()

    active_scene = starting_scene

    while active_scene != None:
        dt = clock.tick(fps)/1000

        pressed_keys = pygame.key.get_pressed()

        filtered_events = []
        for event in pygame.event.get():
            quit_attempt = False
            if event.type == pygame.QUIT:
                quit_attempt = True
            elif event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_ESCAPE:
                    quit_attempt = True
                elif event.key == pygame.K_F4 and alt_pressed:
                    quit_attempt = True
            
            if quit_attempt:
                active_scene.Terminate()
            else:
                filtered_events.append(event)
        
        active_scene.ProcessInputs(filtered_events, pressed_keys)
        active_scene.Update(dt)
        active_scene.Render(canvas)
        
        screen.fill('black')
        screen.blit(canvas,((screen.get_width()-PLAY_WIDTH)/2,(screen.get_height()-PLAY_HEIGHT)/2))

        active_scene =  active_scene.next
        
        pygame.display.flip()




def return_closest_float(f, f_list):
    if not f_list: return None

    closest_float = min(f_list, key=lambda x: abs(x - f))
    return closest_float

    




class SceneBase():
    def __init__(self):
        self.next = self

    def ProcessInputs(self):
        print('uh oh, you didn\'t override this in the child class')
    
    def Update(self, dt):
        print('uh oh, you didn\'t override this in the child class')
    
    def Render(self, screen):
        print('uh oh, you didn\'t override this in the child class')
    
    def SwitchToScene(self, next_scene):
        self.next = next_scene
    
    def Terminate(self):
        self.SwitchToScene(None)


class TextSprite(pygame.sprite.Sprite):
    def __init__(self, text, pos, groups, text_size=30, text_col='black', bg_col=None):
        pygame.font.init()
        super().__init__(groups)

        self.text = text

        self.font = pygame.font.Font(None, text_size)
        self.text_col = text_col
        self.bg_col = bg_col

        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.image = self.font.render(self.text, True, self.text_col, self.bg_col)
        
        self.rect = self.image.get_frect(center = self.pos)
    
    def ChangeColor(self, text_col, bg_col=None):
        self.text_col = text_col
        self.bg_col = bg_col
        self.image = self.font.render(self.text, True, self.text_col, self.bg_col)


class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.can_move = True
        self.lost = False
        self.win = False
        self.speed = 300
        self.steer_speed = 5
        self.angle = 180
        self.dir = pygame.math.Vector2()
        self.throttle = 0
        self.throt_gravity = 0.025
        self.throt_rate = 0.1
        self.pos = pygame.math.Vector2(100,100)

        self.og_image = pygame.image.load('assets/img/car_sprite.png').convert_alpha()
        self.og_image = pygame.transform.smoothscale(self.og_image, (10,20))
        self.image = self.og_image
        self.rect = self.image.get_frect()

        self.mask = pygame.mask.from_surface(self.image)
    
    #str: -1 turn left, 1 turn right.
    def Steer(self, steer):
        self.angle -= steer*self.steer_speed
        if self.angle >= 360: self.angle -= 360
        if self.angle <= -360: self.angle += 360

        rotated_image = pygame.transform.rotate(self.og_image, self.angle)
        new_rect = rotated_image.get_frect(center=self.pos)
        self.image = rotated_image
        self.rect = new_rect

        rad = np.deg2rad(self.angle)
        self.dir.x = np.sin(rad)
        self.dir.y = np.cos(rad)

        self.dir = pygame.math.Vector2.normalize(self.dir) if self.dir.x!=0 and self.dir.y!=0 else self.dir

        self.mask = pygame.mask.from_surface(self.image)
        self.mask_image = self.mask.to_surface()

    
    #throt: -1 move backwards, 1 move forwards
    def Accelerate(self, throt):
        self.throttle += throt*self.throt_rate if -1 < self.throttle < 1 else 0

    
    def CollisionChecks(self, end_point, walls, enemies):
        if self.mask.overlap(end_point.mask, (end_point.rect.centerx-self.pos.x, end_point.rect.centery-self.pos.y)):
            print('AAAHHH!')


    def Update(self, dt):
        if abs(self.throttle)-self.throt_gravity <= 0: self.throttle=0
        if self.throttle>0: self.throttle -= self.throt_gravity
        elif self.throttle<0: self.throttle += self.throt_gravity

        self.pos += self.dir * self.speed * self.throttle * dt
        self.rect.center = self.pos


#need to change the route dictionary to be time:[pos.x, pos.y, angle] to pass the angle along as well
class ShadowPlayer(pygame.sprite.Sprite):
    def __init__(self, route, groups):
        super().__init__(groups)
        self.can_move = True
        self.route = route
        self.pos = pygame.math.Vector2(100,100)

        self.image = pygame.Surface((10,10))
        self.image.fill('blue')
        self.rect = self.image.get_frect()

        print(self.route)
    
    def Update(self, time):
        t_key = return_closest_float(time, list(self.route.keys()))
        self.pos = self.route[t_key]
        self.rect.center = self.pos
        print(f'pos: {self.pos} | cur time: {time} | closest match in route: {t_key}')


class EndPoint(pygame.sprite.Sprite):
    def __init__(self, groups):
            super().__init__(groups)
            self.image = pygame.Surface((20,20))
            self.image.fill('blue')
            self.rect = self.image.get_frect()
            self.mask = pygame.mask.from_surface(self.image)



class TitleScene(SceneBase):    
    def ProcessInputs(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or pygame.K_SPACE:
                    self.SwitchToScene(GameScene())
                

    def Update(self, dt):
        self.text_sprites = pygame.sprite.Group()

        start_text = TextSprite('butterfly pizza delivery!', (PLAY_WIDTH/2, PLAY_HEIGHT/2 -30), [self.text_sprites])
        start_text = TextSprite('press enter to start game!', (PLAY_WIDTH/2, PLAY_HEIGHT/2 +30), [self.text_sprites])
    
    def Render(self, screen):
        screen.fill('white')
        self.text_sprites.draw(screen)
            


class GameScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)

        # self.intro = True
        self.playing = True
        self.paused = False

        self.score = 0
        self.del_time = 5
        self.player_route = {}

        self.all_sprites = pygame.sprite.Group()
        self.text_sprites = pygame.sprite.Group()
        self.end_points = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()

        self.player = Player(self.all_sprites)
        self.end_point = EndPoint([self.all_sprites, self.end_points])

        self.player.pos, self.player.angle = self.generate_route_point()
        self.end_point.rect.center, foo = self.generate_route_point()


    def ProcessInputs(self, events, pressed_keys):
        A_LEFT = pressed_keys[LEFT[0]] or pressed_keys[LEFT[1]]
        A_RIGHT = pressed_keys[RIGHT[0]] or pressed_keys[RIGHT[1]]
        A_UP = pressed_keys[UP[0]] or pressed_keys[UP[1]]
        A_DOWN = pressed_keys[DOWN[0]] or pressed_keys[DOWN[1]]

        pdir = pygame.math.Vector2()
        pdir.x = A_RIGHT - A_LEFT
        pdir.y = A_DOWN - A_UP

        steer = A_RIGHT - A_LEFT
        self.player.Steer(steer)

        throt = A_UP - A_DOWN
        self.player.Accelerate(throt)


        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.pos, self.player.angle = self.generate_route_point()
                    self.end_point.rect.center, foo = self.generate_route_point()


    def Update(self, dt):
        if self.playing:
            # self.del_time -= self.del_time-dt if self.del_time>0 else 0

            self.player.CollisionChecks(self.end_point, self.walls, self.enemies)          


        self.player.Update(dt)

        # self.del_time = self.del_time-dt if self.del_time > 0 else 0
        
        # if self.del_time: 
        #     self.player_route[self.del_time] = pygame.math.Vector2(self.player.pos)
        # elif self.spyeah:
        #     self.sp1 = ShadowPlayer(dict(self.player_route), self.all_sprites)
        #     self.del_time = 5
        #     self.spyeah = False

        # self.player.Update(dt)
        # if not self.spyeah: self.sp1.Update(self.del_time)


    def Render(self, screen):
        screen.fill('green')
        self.all_sprites.draw(screen)


    def generate_route_point(self):
        buf = 30
        pos = pygame.math.Vector2()
        angle = 0
        side = random.randint(0,3) #0-top, 1-right, 2-bottom, 3-left
        
        if side in (0,2):
            pos.x = random.randint(0+buf, PLAY_WIDTH-buf)
            pos.y = 0+buf if side==0 else PLAY_HEIGHT-buf
        if side in (1,3):
            pos.x = 0+buf if side==3 else PLAY_WIDTH-buf
            pos.y = random.randint(0+buf, PLAY_HEIGHT-buf)

        if side==0: angle = 0
        if side==1: angle = 270
        if side==2: angle = 180
        if side==3: angle = 90

        return pos,angle


main(WINDOW_WIDTH, WINDOW_HEIGHT, 60, TitleScene())