#!/usr/bin/env python

'''

BattleX

'''

import pygame  # import pygame
from pygame import mixer  # music
import os  # operating system
import random  # random variables
import csv  # data saving


def checkClick(x1,y1,x2,y2):  # this method checks if a boxed area is clicked
    global mouseDown  # the mouseDown variable prevents double clicking
    pos = pygame.mouse.get_pos()
    if pygame.mouse.get_pressed()[0]:
        if x1 < pos[0] < x1+x2 and y1 < pos[1] < y1+y2:  # python comparison operator is the boss
            mouseDown = True
            return True
    else:
        mouseDown = False
    return False

# initializing music and pygame

mixer.init()
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

# set framerate
clock = pygame.time.Clock()
FPS = 60

#  game variables
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
target_level=1
score = 0
killCount = 0
start_game = False
start_intro = False
bestScores = [0,0,0,0]
mode = 1

# player actions
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

# music and sound
pygame.mixer.music.load('audio/HumbleMatch.ogg')
pygame.mixer.music.set_volume(0.15)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)

# background images
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
# store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
# bullet
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
# grenade
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
# pick up boxes
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health': health_box_img,
    'Ammo'	: ammo_box_img,
    'Grenade'	: grenade_box_img
}

# colors
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

# define font - ArcadeClassic
font = pygame.font.Font('arcadeclassic.ttf', 30) # size = 30

def arcadeFont(size):
    return pygame.font.Font('arcadeclassic.ttf', size)


# set the score
def setScore(s):
    global bestScores
    global score
    global killCount
    if s == score + 100:
        killCount +=1
    if s == 0:
        killCount = 0
    if s >= bestScores[level-1]:
        bestScores[level-1] = s
    score = s

def addScore(s):
    setScore(score+s)

# text engine
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# rectangle engine
def draw_rect(x1,y1,x2,y2,col):
    pygame.draw.rect(screen, col, (x1, y1, x2, y2), 0)

# fill in background
def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))


# function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data


# the Soldier class
class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 100
        self.grenades = grenades
        self.health = 30
        if char_type == "player":
            self.health = 40
        if char_type == "enemy" and level == 3:
            self.health = 1000
            self.grenades = 1e9 ##effectively unlimited
            self.ammo = 1e9  ##effectively unlimited
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # load all images for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            # reset temporary list of images
            temp_list = []
            # count number of files in the folder
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        # animation list

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    # update itself
    def update(self):
        self.update_animation()  # animation
        self.check_alive()  # check if it is alive
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1


    def move(self, moving_left, moving_right):  # movement function
        # reset movement variables
        screen_scroll = 0
        dx = 0  # change of x
        dy = 0  # change of y

        # assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -11
            if pygame.sprite.spritecollide(self, water_group, False):  # if in water, then swimming
                self.vel_y = -11/3
            self.jump = False
            self.in_air = True

        # apply gravity
        self.vel_y += GRAVITY
        if pygame.sprite.spritecollide(self, water_group, False):  # gravity is less in water
            self.vel_y -= GRAVITY*2/3
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        # check for collision - COLLISION DETECTION
        for tile in world.obstacle_list:  # compares to the tile list
            # check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0  # reset dx to 0
                # if the ai has hit a wall then make it turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            # check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if below the ground, i.e. jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, i.e. falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # check for collision with water, then it is now swimming
        if pygame.sprite.spritecollide(self, water_group, False):
            self.in_air=False


        # check for collision with level end

        level_complete = False
        if (pygame.sprite.spritecollide(self, exit_group, False) and (killCount >= ([8,12,0,0][level-1]) or mode != 2)) or (score >= 999 and level == 3):
            level_complete = True



        # check if below the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0  # then die


        # if it goes off the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        # update the player position
        self.rect.x += dx
        self.rect.y += dy

        # update scrolling level based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll <
                    (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

    def shoot(self):  # shooting
        if self.shoot_cooldown == 0 and self.ammo > 0 and (self.char_type=="enemy" or mode != 3 or level == 3):
            self.shoot_cooldown = 10  # cooldown is 1/6 of a second
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            bullet_group.add(bullet)
            # reduce ammo
            self.ammo -= 1
            shot_fx.play()

    def ai(self):  # AI
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) <= 1:  # randomly, it may idle
                self.update_action(0)  # 0: idle
                self.idling = True
                self.idling_counter = 50
            # check if the ai in near the player, or if it is in level 3
            if self.vision.colliderect(player.rect) or (level == 3 and random.randint(1, 10) <= 1):
                # stop running and face the player
                self.update_action(0)  # 0: idle
                # shoot, or possibly grenade depending on the level
                if (random.randint(1,40)==1 or (random.randint(1,10)==1 and level == 3)) and enemy.grenades > 0 and level > 1:
                    grenade = Grenade(self.rect.centerx + (0.5 * self.rect.size[0] * self.direction), \
                                  self.rect.top, self.direction)
                    grenade_group.add(grenade)
                    # reduce grenades
                    self.grenades -= 1
                else:
                    self.shoot()
            else:
                if self.idling == False:  # if it is not idling, then it moves
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)  # 1: run
                    self.move_counter += 1
                    # update ai vision as the enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:  # if it moves enough, it might switch directions
                        self.direction *= -1
                        self.move_counter *= -1
                else:  # if it is idling, it does nothing
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        # scroll
        self.rect.x += screen_scroll

    def update_animation(self):  # animated sprites
        # update animation
        ANIMATION_COOLDOWN = 100
        # update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]  # has a list of animations
        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # if the animation has run out the reset back to the start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):  # does a new action
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):  # check if it is alive
        if self.health <= 0:
            if self.alive == True and self.char_type == "enemy":
                # if you kill an enemy, you gain points!
                if level == 3:
                    addScore(999)
                else:
                    addScore(100)
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):  # drawing a soldier
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():  # the World class
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):  # process through csv data
        self.level_length = len(data[0])
        # iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE  # positioning
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:  # normal tile or box
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:  # water
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:  # random decorative features
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:  # create the main player
                        ammo = 10
                        grenades = 2
                        if level == 3:  # for the final boss
                            ammo = 50
                            grenades = 0

                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, ammo, grenades)
                        health_bar = HealthBar(10, 10, player.health, player.health)  # need a health bar

                    elif tile == 16:  # create the enemies
                        scale = 1.65
                        if level == 3:  # for the final boss
                            scale = 4
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, scale, 2, 10, 5)
                        enemy_group.add(enemy)
                    elif tile == 17:  # create ammo loot
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)

                    elif tile == 18:  # create grenade loot
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)

                    elif tile == 19:  # create health loot
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)

                    elif tile == 20:  # create the level goal!
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar

    def draw(self):  # drawing the tiles
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll  # the screen scroll is used to translate the tile positions
            screen.blit(tile[0], tile[1])

#  random decorative stuff
class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):  # it scrolls
        self.rect.x += screen_scroll

#  water, you can swim, or you can drown!
class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):  # and it scrolls
        self.rect.x += screen_scroll

#  complete the level
class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):  # and it scrolls
        self.rect.x += screen_scroll

#  The ItemBox class is used to gain items and loot. They also score 50 points
class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):  # it scrolls
        # scroll
        self.rect.x += screen_scroll
        # check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            # check what kind of box it was
            if self.item_type == 'Health':  # Health - Gain 12 / 40 HP
                player.health += 12
                if player.health > player.max_health:
                    player.health = player.max_health
                addScore(50)  # +50 pts
            elif self.item_type == 'Ammo':  # Ammo - Gain 5 bullets
                player.ammo += 5
                addScore(50)  # +50 pts
            elif self.item_type == 'Grenade':  # Grenade - Gain 1 grenade
                player.grenades += 1
                addScore(50)  # +50 pts
            # remove the item box
            self.kill()

#  Health Bar of player and boss
class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):  # drawing the health bar
        # update with new health
        self.health = health
        # calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

    def drawBossBar(self, health):  # drawing the boss bar
        global level_complete
        ratio = health / 1000
        if (health <= 0):  # if the boss is dead, the level is completed
            level_complete=True
        scale=3  # the boss bar is bigger
        pygame.draw.rect(screen, BLACK, (self.x - 2 + 300, self.y - 2, 150*scale+4, 24))
        pygame.draw.rect(screen, RED, (self.x + 300, self.y, 150*scale, 20))
        pygame.draw.rect(screen, GREEN, (self.x + 300, self.y, 150 * ratio*scale, 20))
        draw_text('BOSS ', arcadeFont(30), BLACK, 500, 5)  # the boss gets the boss label

# The bullet can hit enemies or you!
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.yvel = 0

    def update(self):  # projectile motion
        # move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll  # x movement
        self.yvel += 0.2  # gravity affected
        self.rect.y += self.yvel  # y movement
        # removes the bullet if it goes off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        # removes the bullet if it collides with the world
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # removes the bullet if it hits a player or enemy
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5  # players take 5 health points of damage
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25  # the boss takes 25 health points of damage
                    if (level != 3):
                        enemy.health += 12.5  # but normal enemies only take 12.5 points of damage
                    self.kill()

# the grenade has an explosion
class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100  # fuse is 1.667 seconds
        self.vel_y = -11  # thrown up
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    # projectile of the grenade
    def update(self):
        self.vel_y += GRAVITY  # gravity affected
        dx = self.direction * self.speed  # change x position
        dy = self.vel_y  # change y position

        # check for collision with the world
        for tile in world.obstacle_list:
            # if it hit a wall, it bounces back
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            # check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                # check if below the ground, it gets knocked down
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, it bounces back up
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        # change grenade position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        # countdown timer
        self.timer -= 1
        if self.timer <= 0:  # when the grenade goes off
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 2)  # it explodes
            explosion_group.add(explosion)
            # do damage to anyone that is nearby
            player.health -= 150000/((self.rect.centerx - player.rect.centerx)**2+(self.rect.centery - player.rect.centery)**2)
            if level == 3: # take double damage on level 3 for players only
                player.health -= 150000 / ((self.rect.centerx - player.rect.centerx) ** 2 + (
                            self.rect.centery - player.rect.centery) ** 2)
            for enemy in enemy_group:  # enemies also take damage
                if level != 3:  # the boss is immune to explosions
                    enemy.health -= 150000/((self.rect.centerx - enemy.rect.centerx)**2+(self.rect.centery - enemy.rect.centery)**2)

#  explosions are everyone's favorite part
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):  # makes an animation list
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]  # cycles through the animated list
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        # scrolling explosion
        self.rect.x += screen_scroll

        EXPLOSION_SPEED = 4
        # update explosion amimation, roughly once per 1/15th of a second
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # if the animation is complete then delete the explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]  # update animation

#  screen fading
class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:  # whole screen fade, middle fade out
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour,
                             (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour,
                             (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:  # vertical screen fade down, such as death
            pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True

        return fade_complete  # returns true if fading is complete


# create screen fades
intro_fade = ScreenFade(1, BLACK, 4)  # opening level
death_fade = ScreenFade(2, BLACK, 10)  # also used for level complete

# create sprite groups, these groups are just list of objects
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# create empty tile list
world_data = []
for row in range(ROWS):  # traverses through the rows
    r = [-1] * COLS
    world_data.append(r)
# load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:  # level loading is awesome!
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()  # create a new world
player, health_bar = world.process_data(world_data)

run = True  # run is the program running
page = 1  # page for menu selection
mouseDown = False  # this is for button pressing

while run:

    clock.tick(FPS)  # 60 frames per second

    if start_game == False and page == 1:  # start screen menu
        # draw menu
        screen.fill(BG)  # background for menu
        # draw the START button
        draw_rect(250,200,300,100,WHITE)
        draw_rect(260, 210, 280, 80, BLACK)
        draw_text("START", arcadeFont(80), WHITE, 295, 210)
        if checkClick(250,200,300,100):
            page = 4

        # draw the INSTRUCTIONS button
        draw_rect(150, 320, 500, 100, WHITE)
        draw_rect(160, 330, 480, 80, BLACK)
        draw_text("INSTRUCTIONS", arcadeFont(60), WHITE, 200, 340)
        if checkClick(150, 320, 500, 100):
            page = 2

        # draw the LEADERBOARD button
        draw_rect(150, 440, 500, 100, WHITE)
        draw_rect(160, 450, 480, 80, BLACK)
        draw_text("LEADERBOARD", arcadeFont(60), WHITE, 220, 460)
        if checkClick(150, 440, 500, 100):
            page = 3

        # draw the QUIT button
        draw_rect(250, 560, 300, 80, WHITE)
        draw_rect(260, 570, 280, 60, BLACK)
        draw_text("QUIT", arcadeFont(60), WHITE, 330, 570)

        # draw the title
        if mouseDown == False and checkClick(250, 560, 300, 80):
            run = False
        draw_text("BattleX",arcadeFont(150),RED,120,50)

    if start_game == False and page == 2:  # page 2 is the How to Play
        screen.fill(BG)
        # add the back button
        draw_rect(30, 30, 200, 100, WHITE)
        draw_rect(40, 40, 180, 80, BLACK)
        draw_text("BACK", arcadeFont(60), WHITE, 60, 50)
        if checkClick(30, 30, 200, 100):
            page = 1
        draw_text("You  are  a  soldier  in  BattleX", arcadeFont(40), BLACK, 100, 150)
        draw_text("Your  goal  is  to  kill  the  enemy", arcadeFont(40), BLACK, 100, 190)
        draw_text("And  make  it  to  the end  of  level", arcadeFont(40), BLACK, 100, 230)

        draw_text("Used  WASD  or  Arrow  Keys  to  move", arcadeFont(40), BLACK, 100, 310)
        draw_text("Spacebar  or  Left  Click  to  Shoot", arcadeFont(40), BLACK, 100, 350)
        draw_text("Q    E    or  Right  Click  to  Grenade", arcadeFont(40), BLACK, 100, 390)

        draw_text("Have  Fun!!!    Credit  goes  to", arcadeFont(40), BLACK, 100, 470)
        draw_text("Ryan  Elyakoubi      Patrick  Hoang", arcadeFont(40), BLACK, 100, 510)
        draw_text("Dev  Upadhyay", arcadeFont(40), BLACK, 100, 550)

    if start_game == False and page == 3:  # Page 3 is the leaderboard
        screen.fill(BG)
        # add the Back button
        draw_rect(30, 30, 200, 100, WHITE)
        draw_rect(40, 40, 180, 80, BLACK)
        draw_text("BACK", arcadeFont(60), WHITE, 60, 50)
        if checkClick(30, 30, 200, 100):
            page = 1
        draw_text("Leaderboard", arcadeFont(60), BLACK, 200, 150)
        draw_text("Level  1  Highscore  is  " + bestScores[0].__str__(), arcadeFont(60), BLACK, 30, 250)
        draw_text("Level  2  Highscore  is  " + bestScores[1].__str__(), arcadeFont(60), BLACK, 30, 310)
        draw_text("Level  3  Highscore  is  " + bestScores[2].__str__(), arcadeFont(60), BLACK, 30, 370)

    if start_game == False and page == 4: # page 4 is the level select page
        screen.fill(BG)
        # add the back button
        draw_rect(30, 30, 200, 100, WHITE)
        draw_rect(40, 40, 180, 80, BLACK)
        draw_text("BACK", arcadeFont(60), WHITE, 60, 50)
        if checkClick(30, 30, 200, 100):
            page = 1

        # what level is it?
        draw_rect(150, 200, 500, 100, WHITE)
        draw_rect(160, 210, 480, 80, BLACK)
        draw_text("Level  " + level.__str__(), arcadeFont(80), WHITE, 250, 210)

        # level cycling
        if mouseDown == False and checkClick(150, 200, 500, 100):
            level += 1
            if (level == 4):
                level = 1

        # what mode is it?
        draw_rect(150, 350, 500, 100, WHITE)
        draw_rect(160, 360, 480, 80, BLACK)
        if mode == 1: # normal
            draw_text("Normal", arcadeFont(80), WHITE, 250, 360)
            draw_text("Normal  Mode  is  the  basic  mode", arcadeFont(40), BLACK, 100, 470)
        if mode == 2: # serial
            draw_text("Serial", arcadeFont(80), WHITE, 250, 360)
            draw_text("You  must  kill  all  enemies", arcadeFont(40), BLACK, 100, 470)
        if mode == 3: # pacifist
            draw_text("Pacifist", arcadeFont(80), WHITE, 250, 360)
            draw_text("You  can  only  fight  on  lvl  3", arcadeFont(40), BLACK, 100, 470)
        if mouseDown == False and checkClick(150, 350, 500, 100):  # mode cycling
            mode += 1
            if (mode == 4):
                mode = 1

        # draw the play button
        draw_rect(250, 520, 300, 100, WHITE)
        draw_rect(260, 530, 280, 80, BLACK)
        draw_text("PLAY", arcadeFont(80), WHITE, 295, 530)

        if checkClick(250, 520, 300, 100):  # play the game
            start_game = True
            start_intro = True
            target_level=level
            level=1

    if start_game == False and page == 5:  # page 5 is the winner page
        screen.fill(BLACK)
        draw_text("Game Beaten!", arcadeFont(80), GREEN, 150, 210)  # you won the game
        draw_text("You  defeated  the  final  boss", arcadeFont(40), WHITE, 100, 370)
        draw_text("Thank  you  for  playing", arcadeFont(40), WHITE, 100, 420)

        draw_rect(250, 520, 300, 100, WHITE)
        draw_rect(260, 530, 280, 80, BLACK)
        draw_text("MENU", arcadeFont(80), WHITE, 295, 530)  # go to menu
        if checkClick(250, 520, 300, 100):
            page = 1

    if start_game == True:  # if the game is running
        # update background

        draw_bg()
        # draw the world
        world.draw()
        # update player health
        health_bar.draw(player.health)


        # show the ammo
        draw_text('AMMO', arcadeFont(30), WHITE, 10, 35)
        for x in range(player.ammo):
            screen.blit(bullet_img, (90 + (x * 10), 45))
        # show the grenades
        draw_text('GRENADES', arcadeFont(30), WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (155 + (x * 15), 70))
        # show the score
        draw_text('SCORE       ' + score.__str__(), arcadeFont(30), WHITE, 10, 85)

        # update the player
        player.update()
        player.draw()

        for enemy in enemy_group:  # update the enemies, such as AI
            enemy.ai()
            enemy.update()
            enemy.draw()
            if level == 3:  # draw a boss bar is needed
                health_bar.drawBossBar(enemy.health)

        # update plus draw all of these extra groups
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()
        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        # intro fading animation
        if start_intro == True:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0

        # player actions
        if player.alive and not (level == 3 and level_complete):
            # shooting
            if shoot:
                player.shoot()
            # grenades
            elif grenade and grenade_thrown == False and player.grenades > 0 and (mode != 3):
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
                                  player.rect.top, player.direction)
                grenade_group.add(grenade)
                # reduce grenades
                player.grenades -= 1
                grenade_thrown = True
            if player.in_air:
                player.update_action(2)  # 2: jumping
            elif moving_left or moving_right:
                player.update_action(1)  # 1: running
            else:
                player.update_action(0)  # 0: idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            # check if player has completed the level
            if level_complete or target_level > level:
                start_intro = True
                level_complete = False
                setScore(0)  # reset score
                level += 1  # increment the level
                bg_scroll = 0
                if True:  # ignore the If True
                    world_data = reset_level()
                    if level <= MAX_LEVELS:
                        # load in the level data
                        with open(f'level{level}_data.csv', newline='') as csvfile:
                            reader = csv.reader(csvfile, delimiter=',')
                            for x, row in enumerate(reader):
                                for y, tile in enumerate(row):
                                    world_data[x][y] = int(tile)
                        world = World()
                        player, health_bar = world.process_data(world_data)
        else:  # this is used if player is either dead OR completed the game
            screen_scroll = 0

            if death_fade.fade():
                if player.alive:  # if completed the game
                    page = 5
                    setScore(0)
                    level = 1  # reset the stuff

                    bg_scroll = 0
                    if True:
                        world_data = reset_level()
                        if level <= MAX_LEVELS:
                            # load in level data and create world
                            with open(f'level{level}_data.csv', newline='') as csvfile:
                                reader = csv.reader(csvfile, delimiter=',')
                                for x, row in enumerate(reader):
                                    for y, tile in enumerate(row):
                                        world_data[x][y] = int(tile)
                            world = World()
                            player, health_bar = world.process_data(world_data)

                    start_game=False

                else:  # otherwise, the player must be dead
                    draw_text("You   died!", arcadeFont(100), RED, 180, 150)
                    # death screen
                    draw_rect(150, 320, 500, 100, WHITE)
                    draw_rect(160, 330, 480, 80, BLACK)
                    draw_text("Restart", arcadeFont(60), WHITE, 290, 340)  # restart button
                    if checkClick(150, 320, 500, 100):  # restarts the level

                        death_fade.fade_counter = 0
                        start_intro = True
                        bg_scroll = 0
                        setScore(0)
                        world_data = reset_level()
                        # reload the level when restarting
                        with open(f'level{level}_data.csv', newline='') as csvfile:
                            reader = csv.reader(csvfile, delimiter=',')
                            for x, row in enumerate(reader):
                                for y, tile in enumerate(row):
                                    world_data[x][y] = int(tile)
                        world = World()
                        player, health_bar = world.process_data(world_data)

    for event in pygame.event.get():  # possible events
        # quit game
        if event.type == pygame.QUIT:
            run = False  # stop running
        # keyboard pressing
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:  # A or Left = Move Left
                moving_left = True
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:  # D or Right = Move Right
                moving_right = True
            if event.key == pygame.K_SPACE:  # Spacebar does shooting
                shoot = True
            if event.key == pygame.K_q or event.key == pygame.K_e:  # Q or E for grenades
                grenade = True
            if (event.key == pygame.K_w or event.key == pygame.K_UP) and player.alive:  # W or Up is jumping, can't jump if you are dead
                player.jump = True
                jump_fx.play()
            if event.key == pygame.K_ESCAPE:  # escape = Leave the game - QUIT
                run = False

        if event.type == pygame.MOUSEBUTTONDOWN:  # mouse press
            if event.button == 1:  # Left click for shoot
                shoot = True
            if event.button == 3:  # Right click for grenade
                grenade = True
        if event.type == pygame.MOUSEBUTTONUP:  # mouse release
            if event.button == 1:  # Left click for shoot
                shoot = False
            if event.button == 3:  # Right click for grenade
                grenade = False
                grenade_thrown = False


        # keyboard  released, same as above
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                moving_left = False
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q or event.key == pygame.K_e:
                grenade = False
                grenade_thrown = False

    pygame.display.update()  # update the display

pygame.quit()  # after the program is finished, QUIT the game and exit!
