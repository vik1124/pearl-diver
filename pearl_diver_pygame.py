#!/usr/bin/env python3
"""Pearl Diver: a turn-based Pygame adaptation. No external artwork required."""
import argparse
import math
import random
import textwrap
from dataclasses import dataclass, field

DATA = [1,0,0,4,0,2,0,9,0,4,0,0,4,0,2,10,
        7,0,0,4,0,0,7,0,3,9,0,0,0,7,0,7,
        0,3,0,5,1,0,2,0,8,0,0,9,2,0,3,0,
        5,0,8,5,0,4,5,0,0,4,6,0,5,0,0,5]
CREATURES = {1: ('OCTOPUS',18), 2: ('SHARK',32),
             3: ('GIANT SQUID',24), 7: ('PIRANHAS',14)}

@dataclass
class Game:
    rng: random.Random = field(default_factory=random.Random)
    location: int = 3
    strength: int = 90
    pearls: int = 0
    sea: list = field(default_factory=lambda: [0,0] + DATA.copy())
    visited: set = field(default_factory=set)
    mode: str = 'explore'
    title: str = 'CLEAR WATER'
    messages: list = field(default_factory=list)
    creature: str = ''
    health: int = 0
    max_health: int = 1
    escape_cost: int = 0
    battle_elapsed: float = 0
    flash: float = 0
    visual: int = 0

    def say(self, message):
        self.messages.append(message)
        self.messages = self.messages[-4:]

    def finish(self, won=False):
        self.mode = 'win' if won else 'dead'
        self.title = "YOU'RE RICH!" if won else 'DAVY JONES\' LOCKER'
        self.say('You return to your boat with your treasure.' if won else
                 'You fall to a watery grave. Your dive is over.')

    def alive(self):
        if self.strength <= 0:
            self.finish()
            return False
        return True

    def enter(self):
        self.mode = 'explore'
        self.visited.add(self.location)
        item = self.sea[self.location]
        self.visual = item
        if item in CREATURES:
            self.creature, self.health = CREATURES[item]
            self.max_health = self.health
            self.escape_cost = self.rng.randint(1,10)
            self.mode = 'encounter'
            self.title = self.creature
            self.say('A creature blocks your path. Fight or try to escape?')
        elif item == 0:
            self.title = 'CLEAR WATER'
            self.say('Nothing here. Choose your next direction.')
        elif item == 4:
            self.title = 'TANGLED IN SEAWEED'
            self.strength -= 5
            self.say('You untangle yourself, losing 5 strength.')
            self.alive()
        elif item == 5:
            self.title = 'A PEARL!'
            self.pearls += 1
            self.sea[self.location] = 0
            self.say('You collect an oyster pearl. Return to the boat with five.')
        elif item == 6:
            self.title = 'AN OLD CHEST'
            self.mode = 'chest'
            self.say('Open it? Treasure awaits, but a spirit may kill you.')
        elif item == 8:
            self.title = 'OXYGEN CYLINDER'
            self.strength += 15
            self.sea[self.location] = 0
            self.say('Fresh oxygen restores 15 strength.')
        elif item == 9:
            self.title = 'A SHOAL OF FISH'
            self.say('These fish are harmless. Swim on.')
        elif item == 10:
            self.title = 'YOUR BOAT'
            if self.pearls >= 5:
                self.finish(True)
            else:
                self.say(f'You need {5-self.pearls} more pearls before retiring rich.')

    def move(self, direction):
        if self.mode != 'explore':
            return
        old = self.location
        # Retain the original linear map, including its unusual E/W direction.
        if direction == 'N' and old > 8: self.location -= 8
        elif direction == 'S' and old < 56: self.location += 8
        elif direction == 'E' and old > 1: self.location -= 1
        elif direction == 'W' and old < 64: self.location += 1
        self.strength -= 1
        if self.alive():
            self.enter()
            if old == self.location:
                self.say('The edge blocks you. The attempt still costs 1 strength.')

    def action(self, action):
        if self.mode == 'encounter':
            if action == 'fight':
                self.mode = 'battle'
                self.battle_elapsed = 0
                self.say('Let the battle begin!')
            elif action == 'escape':
                if self.rng.random() > .5:
                    self.say('The creature catches you as you try to escape!')
                    self.finish()
                    return
                self.strength -= self.escape_cost
                self.say(f'You escape, losing {self.escape_cost} strength.')
                if not self.alive(): return
                p = self.location
                for target, allowed in ((p-1,p>1),(p+1,p<64),
                                        (p+8,p<56),(p-8,p>8)):
                    if allowed and self.sea[target] == 0:
                        self.location = target
                        break
                else:
                    self.sea[p] = 0
                self.visited.add(self.location)
                self.visual = 0
                self.title = 'ESCAPED'
                self.mode = 'explore'
        elif self.mode == 'chest':
            if action == 'open':
                if self.rng.random() > .66:
                    self.say('A hideous spirit leaps out of the chest!')
                    self.finish()
                else:
                    self.pearls = 5
                    self.mode = 'explore'
                    self.title = 'TREASURE FOUND'
                    self.say('You have enough treasure! Find your boat.')
            elif action == 'leave':
                self.mode = 'explore'
                self.say('You leave the chest closed.')

    def update(self, dt):
        self.flash = max(0, self.flash-dt)
        if self.mode != 'battle': return
        self.battle_elapsed += dt
        if self.battle_elapsed < .35: return
        self.battle_elapsed -= .35
        if self.rng.random() > .66:
            self.strength -= 1
            self.flash = .15
            self.say('The creature hurts you! (-1 strength)')
        if self.rng.random() < .34:
            damage = self.rng.randint(1,4)
            self.health -= damage
            self.say(f'Your attack deals {damage} damage.')
        if not self.alive(): return
        if self.health <= 0:
            self.sea[self.location] = 0
            self.visual = 0
            self.mode = 'explore'
            self.title = 'CREATURE DEFEATED'
            self.say('You won the battle. The way is clear.')


def main():
    import pygame as pg
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--smoke-test', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    pg.init()
    screen = pg.display.set_mode((1000,740))
    pg.display.set_caption('Pearl Diver')
    clock = pg.time.Clock()
    font = pg.font.Font(None,25)
    small = pg.font.Font(None,20)
    large = pg.font.Font(None,44)
    white, cyan, gold = (220,240,247), (78,215,219), (255,204,100)
    game = Game(rng=random.Random(args.seed))
    game.enter()
    buttons = []

    def label(text,x,y,color=white,f=font):
        screen.blit(f.render(text,True,color),(x,y))

    def button(text, rect, action):
        r = pg.Rect(rect)
        hover = r.collidepoint(pg.mouse.get_pos())
        pg.draw.rect(screen,(35,105,128) if hover else (22,65,86),r,border_radius=8)
        pg.draw.rect(screen,cyan,r,1,border_radius=8)
        label(text,r.x+12,r.y+12)
        buttons.append((r,action))

    def dispatch(action):
        nonlocal game
        if action == 'restart':
            game = Game(rng=random.Random(args.seed)); game.enter()
        elif action in {'N','S','E','W'}: game.move(action)
        else: game.action(action)

    def fish(x,y,size,color):
        pg.draw.ellipse(screen,color,(x-size,y-size//2,size*2,size))
        pg.draw.polygon(screen,color,[(x+size-2,y),(x+size*2,y-size),(x+size*2,y+size)])
        pg.draw.circle(screen,(5,20,35),(x-size//2,y-2),3)

    running = True
    frames = 0
    while running:
        dt = min(clock.tick(60)/1000,.1)
        for event in pg.event.get():
            if event.type == pg.QUIT: running = False
            elif event.type == pg.KEYDOWN:
                key = event.key
                if key in (pg.K_ESCAPE,pg.K_q): running = False
                elif key == pg.K_r: dispatch('restart')
                elif game.mode == 'explore':
                    directions = {pg.K_UP:'N',pg.K_w:'N',pg.K_DOWN:'S',pg.K_s:'S',
                                  pg.K_LEFT:'W',pg.K_a:'W',pg.K_RIGHT:'E',pg.K_d:'E'}
                    if key in directions: dispatch(directions[key])
                elif game.mode == 'encounter':
                    if key == pg.K_f: dispatch('fight')
                    elif key == pg.K_s: dispatch('escape')
                elif game.mode == 'chest':
                    if key == pg.K_y: dispatch('open')
                    elif key == pg.K_n: dispatch('leave')
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                for rect, action in buttons:
                    if rect.collidepoint(event.pos):
                        dispatch(action); break
        game.update(dt)
        buttons = []
        screen.fill((7,17,31))
        label('PEARL DIVER',28,22,cyan,large)
        label('A ZX SPECTRUM ADVENTURE / PYTHON EDITION',30,66,f=small)
        label(f'STRENGTH  {game.strength}',590,28,gold)
        label(f'PEARLS  {game.pearls} / 5',800,28,gold)
        # Underwater scene.
        depth = (game.location-1)//16
        for y in range(105,440):
            shade = int((y-105)/335*25)
            pg.draw.line(screen,(8,65-depth*8-shade//2,100-depth*10-shade),(24,y),(682,y))
        pg.draw.rect(screen,(25,57,62),(24,414,659,26))
        t = pg.time.get_ticks()/1000
        for i in range(14):
            x = 45+i*45
            y = 420-int((t*24+i*27)%300)
            pg.draw.circle(screen,(50,125,151),(x,y),3,1)
        # Diver: mask, tank, body and fins.
        bob = int(math.sin(t*2)*4)
        pg.draw.rect(screen,gold,(164,266+bob,66,22),border_radius=8)
        pg.draw.ellipse(screen,cyan,(214,244+bob,40,32))
        pg.draw.rect(screen,(8,30,45),(235,251+bob,25,13),border_radius=3)
        pg.draw.rect(screen,(135,151,163),(177,255+bob,35,14),border_radius=4)
        pg.draw.line(screen,gold,(170,276+bob),(145,295+bob),9)
        pg.draw.line(screen,cyan,(145,295+bob),(126,296+bob),8)
        item = game.visual
        if item in (1,3):
            color = (190,112,210) if item==1 else (218,109,130)
            pg.draw.ellipse(screen,color,(460,220,75,85))
            for i in range(6):
                pts=[(470+i*10,285),(460+i*14,320),(450+i*18+int(math.sin(t*3+i)*9),351)]
                pg.draw.lines(screen,color,False,pts,6)
            pg.draw.circle(screen,white,(480,249),7)
            pg.draw.circle(screen,(10,20,35),(478,249),3)
        elif item in (2,7,9):
            for i in range(1 if item==2 else 6):
                fish(490+(i%3)*40,270+(i//3)*45,48 if item==2 else 13,
                     (155,180,195) if item==2 else gold)
            if item==2:
                pg.draw.polygon(screen,(155,180,195),[(475,255),(500,220),(510,260)])
        elif item==4:
            for i in range(9):
                pts=[(440+i*18+int(math.sin(t*2+j+i)*9),414-j*20) for j in range(6)]
                pg.draw.lines(screen,(63,184,126),False,pts,7)
        elif item==5:
            pg.draw.ellipse(screen,(201,133,169),(462,344,84,42))
            pg.draw.circle(screen,white,(504,345),14)
        elif item==6:
            pg.draw.rect(screen,(149,94,53),(455,324,96,67),border_radius=6)
            for x in (470,530): pg.draw.rect(screen,gold,(x,324,8,67))
            pg.draw.rect(screen,gold,(497,346,15,16))
        elif item==8:
            pg.draw.rect(screen,cyan,(483,279,36,95),border_radius=14)
            pg.draw.rect(screen,gold,(491,267,20,13))
            label('O2',488,310,(6,33,49))
        elif item==10:
            pg.draw.polygon(screen,gold,[(429,200),(576,200),(548,232),(453,232)])
            pg.draw.line(screen,white,(495,200),(495,140),4)
            pg.draw.polygon(screen,white,[(500,142),(500,190),(544,190)])
        if game.flash>0: pg.draw.rect(screen,(240,85,94),(24,105,659,335),5)
        if game.mode in ('encounter','battle'):
            label(f'{game.creature}  {max(0,game.health)} HP',420,120,gold)
            pg.draw.rect(screen,(40,40,55),(420,148,220,8))
            pg.draw.rect(screen,(230,112,125),(420,148,int(220*max(0,game.health)/game.max_health),8))
        # Explored cells only. Reverse columns to match the original E/W rules.
        label('DIVE CHART',716,110,cyan)
        for cell in range(1,65):
            row,col=divmod(cell-1,8)
            rect=pg.Rect(716+(7-col)*30,146+row*30,26,26)
            color=(29,74,94) if cell in game.visited else (15,35,51)
            pg.draw.rect(screen,color,rect,border_radius=3)
            if cell==game.location: pg.draw.rect(screen,gold,rect,3,border_radius=3)
            elif cell in game.visited and game.sea[cell]==10: label('B',rect.x+7,rect.y+4,cyan,small)
        depth_name=('SHALLOWS','SEVERAL FATHOMS','MURKY DEPTHS','OCEAN FLOOR')[depth]
        label(depth_name,716,400,gold,small)
        label(f'Cell {game.location} / N is shallower',716,424,f=small)
        label(game.title,28,463,cyan,large)
        line_y=512
        for message in game.messages[-3:]:
            for line in textwrap.wrap(message,88):
                label(line,30,line_y); line_y+=23
        if game.mode=='explore':
            for i,direction in enumerate(('N','S','W','E')):
                button(direction,(28+i*68,644,58,44),direction)
            label('Arrow keys / WASD to swim',330,658,f=small)
        elif game.mode=='encounter':
            button('F - Fight',(28,644,155,44),'fight')
            button('S - Escape',(198,644,165,44),'escape')
        elif game.mode=='chest':
            button('Y - Open',(28,644,155,44),'open')
            button('N - Leave',(198,644,165,44),'leave')
        elif game.mode=='battle': label('Battle in progress...',30,658,gold)
        else: label('Dive complete. Press R to try again.',30,658,gold)
        button('R - Restart',(790,644,180,44),'restart')
        label('Collect five pearls and return to the boat.   |   Q / Esc: quit',28,711,f=small)
        pg.display.flip()
        frames += 1
        if args.smoke_test and frames>=3: running=False
    pg.quit()

if __name__=='__main__':
    main()
