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
PLAY_WIDTH, PLAY_HEIGHT = 600,600
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
                if event.key == pygame.K_F4 and alt_pressed:
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
        self.lose = False
        self.win = False
        self.speed = 280
        self.steer_speed = 7
        self.angle = 180
        self.dir = pygame.math.Vector2()
        self.throttle = 0
        self.throt_gravity = 0.025
        self.throt_rate = 0.1
        self.velocity = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(100,100)
        self.precheck_angle = self.angle
        self.precheck_pos = self.pos
        self.collided_with_wall = False

        self.end_point = None
        self.enemies = None
        self.walls = None

        self.og_image = pygame.image.load('assets/img/butterfly.jpeg').convert_alpha()
        self.og_image = pygame.transform.smoothscale(self.og_image, (15,20))
        self.image = self.og_image
        self.rect = self.image.get_frect()

        self.mask = pygame.mask.from_surface(self.image)
        self.mask_image = self.mask.to_surface()


    def Update(self, dt):
        if abs(self.throttle)-self.throt_gravity <= 0: self.throttle=0
        if self.throttle>0: self.throttle -= self.throt_gravity
        elif self.throttle<0: self.throttle += self.throt_gravity

        self.precheck_pos = pygame.math.Vector2(self.pos)
        if not self.lose: self.velocity = self.dir * self.speed * self.throttle * dt
        else: self.velocity = pygame.math.Vector2(0,0)

        self.pos.x += self.velocity.x
        self.CollisionChecks()
        if self.pos.x <= 0+self.rect.width: self.collided_with_wall=True
        if self.pos.x >= PLAY_WIDTH-self.rect.width: self.collided_with_wall=True
        if self.collided_with_wall: self.pos.x = self.precheck_pos.x

        self.pos.y += self.velocity.y
        self.CollisionChecks()
        if self.pos.y <= 0+self.rect.height: self.collided_with_wall=True
        if self.pos.y >= PLAY_HEIGHT-self.rect.height: self.collided_with_wall=True
        if self.collided_with_wall: self.pos.y = self.precheck_pos.y

        self.rect.center = self.pos

    
    def CollisionChecks(self):
        if self.end_point==None: return
        overlap = (self.end_point.rect.left - (self.pos.x-self.rect.width/2), self.end_point.rect.top - (self.pos.y-self.rect.width/2))
        if self.mask.overlap(self.end_point.mask, (self.end_point.rect.centerx-self.pos.x, self.end_point.rect.centery-self.pos.y)):
            self.win = True
        
        # if self.mask.overlap(self.wall.mask, (self.wall.rect.centerx-self.pos.x, self.wall.rect.centery-self.pos.y)): #I HAVE NO IDEA WHY THIS NEEDS rect.left and rect.top instead of centerx and centery, I can't tell the difference between this and EndPoint but whatever
        #     self.collided_with_wall = True
        # else: self.collided_with_wall = False

        self.collided_with_wall = False
        if self.walls==None: return
        for wall in self.walls:
            overlap = (wall.rect.left - (self.pos.x-self.rect.width/2), wall.rect.top - (self.pos.y-self.rect.height/2))
            if self.mask.overlap(wall.mask, overlap): 
                self.collided_with_wall = True
                break
            else: self.collided_with_wall = False
        
        if self.enemies==None: return
        for enemy in self.enemies:
            overlap = (enemy.rect.left - (self.pos.x-self.rect.width/2), enemy.rect.top - (self.pos.y-self.rect.height/2))
            if self.mask.overlap(enemy.mask, overlap):
                self.lose = True
                break


     #str: -1 turn left, 1 turn right.
    def Steer(self, steer):
        self.precheck_angle = self.angle
        self.angle -= steer*self.steer_speed
        if self.angle >= 360: self.angle -= 360
        if self.angle <= -360: self.angle += 360

        # self.CollisionChecks()
        # if self.collided_with_wall: self.angle = self.precheck_angle

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



#need to change the route dictionary to be time:[pos.x, pos.y, angle] to pass the angle along as well
class Enemy(pygame.sprite.Sprite):
    def __init__(self, route, groups):
        super().__init__(groups)
        self.can_move = True
        self.route = route
        self.pos = pygame.math.Vector2(100,100)
        self.angle = 180

        self.og_image = pygame.Surface((10,20)).convert_alpha()
        self.og_image.fill('red')
        self.image = self.og_image
        self.rect = self.image.get_frect()

        self.mask = pygame.mask.from_surface(self.image)
    
    def Update(self, time):
        t_key = return_closest_float(time, list(self.route.keys()))
        self.pos.x = self.route[t_key][0]
        self.pos.y = self.route[t_key][1]
        self.angle = self.route[t_key][2]

        self.rect.center = self.pos
        self.Steer(self.angle)

        if self.route[t_key][3]: self.kill()


    def Steer(self, angle):
        rotated_image = pygame.transform.rotate(self.og_image, angle)
        new_rect = rotated_image.get_frect(center=self.pos)
        self.image = rotated_image
        self.rect = new_rect

        self.mask = pygame.mask.from_surface(self.image)


class EndPoint(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.Surface((30,30))
        self.image.fill('blue')
        self.rect = self.image.get_frect()
        self.mask = pygame.mask.from_surface(self.image)


class DeadEndPoint(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.Surface((30,30))
        self.image.fill('grey')
        self.rect = self.image.get_frect()
        self.mask = pygame.mask.from_surface(self.image)


class Wall(pygame.sprite.Sprite):
    def __init__(self, groups, image=None, width=20, height=20): #for some reason only works with 20x20y? no idea why the collision stops working at higher scale it's weird
        super().__init__(groups)
        if image==None: 
            self.image = pygame.Surface((width,height))
            self.image.fill('white')
        else: 
            self.image = pygame.image.load(image).convert_alpha()
            self.image = pygame.transform.smoothscale(self.image, (width,height))
            
        self.rect = self.image.get_frect()
        self.rect.topleft = (0,0)

        self.mask = pygame.mask.from_surface(self.image)
        self.mask_image = self.mask.to_surface()



class TitleScene(SceneBase):    
    def ProcessInputs(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.SwitchToScene(GameScene())
                

    def Update(self, dt):
        self.text_sprites = pygame.sprite.Group()

        start_text = TextSprite('butterfly pizza delivery!', (PLAY_WIDTH/2, PLAY_HEIGHT/2 -30), [self.text_sprites])
        start_text = TextSprite('press [enter] to start game!', (PLAY_WIDTH/2, PLAY_HEIGHT/2 +30), [self.text_sprites])
    
    def Render(self, screen):
        screen.fill('white')
        self.text_sprites.draw(screen)
            


class GameScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)

        self.intro = True
        self.playing = False
        self.outro = False
        self.paused = False

        self.starting_intro_time = 2.5
        self.intro_time = self.starting_intro_time
        self.score = 0
        self.level = -1
        self.starting_go_time = 6
        self.go_time = self.starting_go_time

        self.player_route = {}
        self.routes = []

        self.all_sprites = pygame.sprite.Group()
        self.text_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.dead_end_points = pygame.sprite.Group()

        self.player = None #defined in setup
        self.end_point = None #defined in setup

        #self.wall1 = Wall([self.all_sprites, self.walls], 'assets/collision-maps/L_t1_collision-map.png', PLAY_WIDTH, PLAY_HEIGHT)
        self.Setup()


    def ProcessInputs(self, events, pressed_keys):
        A_LEFT = pressed_keys[LEFT[0]] or pressed_keys[LEFT[1]]
        A_RIGHT = pressed_keys[RIGHT[0]] or pressed_keys[RIGHT[1]]
        A_UP = pressed_keys[UP[0]] or pressed_keys[UP[1]]
        A_DOWN = pressed_keys[DOWN[0]] or pressed_keys[DOWN[1]]

        steer = A_RIGHT - A_LEFT
        throt = A_UP - A_DOWN

        if self.playing and not self.outro:
            self.player.Steer(steer)
            self.player.Accelerate(throt)


        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    if self.player.win: self.go_time = 0
                    if self.paused: self.paused = False

                if event.key in [pygame.K_ESCAPE]:
                    self.paused=False if self.paused else True
                
                if event.key in [pygame.K_r]:
                    if self.paused or self.player.lose: self.Reset()



    def Update(self, dt):
        self.del_time_text = TextSprite(f'{self.go_time:.2f}', (PLAY_WIDTH/2, 15), [self.text_sprites], 30, 'white', 'black')
        self.del_time_text = TextSprite(f'level: {self.level}', (PLAY_WIDTH/2, 45), [self.text_sprites], 20, 'white')
        
        if self.intro:
            self.intro_time -= dt
            if self.intro_time <= 0: 
                self.intro=False
                self.playing = True
            
            self.instruc_text = TextSprite(f'deliver the pizza to the blue square!', (PLAY_WIDTH/2, PLAY_HEIGHT-15), [self.text_sprites], 30, 'blue', 'white')

        if self.paused:
            self.playing = False
            self.instruc_text = TextSprite(f'paused', (PLAY_WIDTH/2, PLAY_HEIGHT/2), [self.text_sprites], 30, 'black', 'white')
            self.instruc_text = TextSprite(f'press [esc] to keep playing', (PLAY_WIDTH/2, PLAY_HEIGHT/2+30), [self.text_sprites], 20, 'black', 'white')
            self.instruc_text = TextSprite(f'or press [r] to reset', (PLAY_WIDTH/2, PLAY_HEIGHT/2+45), [self.text_sprites], 20, 'black', 'white')

        elif not self.intro:
            self.playing = True

        if self.playing:
            self.player_route[self.go_time] = [self.player.pos.x, self.player.pos.y, self.player.angle, int(self.player.win)]
            
            self.go_time = self.go_time-dt if self.go_time>0 else 0
            if self.go_time==0 and not self.player.win: 
                self.player.lose = True
                print('loooost')

            #inefficient but it works fuck off
            self.player.end_point = self.end_point
            self.player.enemies = self.enemies
            self.player.walls = self.walls


            if self.player.win:
                if self.player in self.all_sprites:
                    self.routes.append(dict(self.player_route))
                    self.score += 1
                self.outro = True
                self.player.kill()

            if self.player.lose:
                if self.go_time >= self.starting_go_time-1: 
                    self.player.lose = False
                else:
                    print('loser')
                    self.playing = False


        if self.outro:
            self.instruc_text = TextSprite(f'good job!', (PLAY_WIDTH/2, PLAY_HEIGHT/2), [self.text_sprites], 30, 'green', 'white')
            if self.go_time<=0: self.Setup()


        if self.player.lose:
            if self.go_time == 0:
                self.instruc_text = TextSprite(f'you took too long and let the pizza get cold!', (PLAY_WIDTH/2, PLAY_HEIGHT/2), [self.text_sprites], 30, 'red', 'white')
            else:
                self.instruc_text = TextSprite(f'oops, you crashed!', (PLAY_WIDTH/2, PLAY_HEIGHT/2), [self.text_sprites], 30, 'red', 'white')
            self.instruc_text = TextSprite(f'press [r] to play again', (PLAY_WIDTH/2, PLAY_HEIGHT/2+30), [self.text_sprites], 30, 'red', 'white')


        self.player.Update(dt)
        for e in self.enemies: 
            e.Update(self.go_time)



    def Render(self, screen):
        screen.fill('green')
        self.dead_end_points.draw(screen) #I want player to be rendered on top of this
        self.all_sprites.draw(screen)
        self.text_sprites.draw(screen)

        for i in self.text_sprites: i.kill()



    def Setup(self):
        self.player_route = {}
        self.intro = True
        self.intro_time = self.starting_intro_time
        self.playing = False
        self.outro = False
        self.paused = False
        self.go_time = self.starting_go_time
        self.level+=1

        if self.player in self.all_sprites: self.player.kill()
        if self.end_point in self.all_sprites: 
            dead_end_point = DeadEndPoint(self.dead_end_points)
            dead_end_point.rect.center = self.end_point.rect.center
            self.end_point.kill()

        self.player = Player(self.all_sprites)
        self.end_point = EndPoint([self.all_sprites])

        self.player.pos, self.player.angle = self.generate_route_point()
        self.end_point.rect.center, foo = self.generate_route_point()

        for i in self.enemies: i.kill()
        for i in range(self.score):
            enemy = Enemy(dict(self.routes[i]), [self.all_sprites, self.enemies])


    def Reset(self):
        self.SwitchToScene(GameScene())


    def generate_route_point(self):
        buf = 35
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