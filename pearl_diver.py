#!/usr/bin/env python3
"""Pearl Diver: a standard-library Python translation of the supplied ZX tape."""
import argparse
import random
from dataclasses import dataclass, field

# BASIC reads these into A(2)..A(65), leaving A(1) empty.
DATA = [
    1,0,0,4,0,2,0,9,0,4,0,0,4,0,2,10,
    7,0,0,4,0,0,7,0,3,9,0,0,0,7,0,7,
    0,3,0,5,1,0,2,0,8,0,0,9,2,0,3,0,
    5,0,8,5,0,4,5,0,0,4,6,0,5,0,0,5,
]
CREATURES = {1: ('an octopus',18), 2: ('a maneating shark',32),
             3: ('a giant squid',24), 7: ('piranhas',14)}

@dataclass
class Game:
    rng: random.Random = field(default_factory=random.Random)
    location: int = 3
    strength: int = 90
    treasure: int = 0
    sea: list = field(default_factory=lambda: [0, 0] + DATA.copy())
    ended: bool = False
    won: bool = False

    def finish(self, won=False):
        self.ended = True
        self.won = won
        if won:
            print("\nYou're Rich! You return to your boat with your treasure.")
        else:
            print("\nR.I.P. You fall to a watery grave.")
            print("Your greed for pearls has left you in Davy Jones' Locker.")

    def check_strength(self):
        if self.strength <= 0:
            self.finish()
            return False
        return True

    def move(self, direction):
        # Preserve the original linear-map rules, including E/W row crossings.
        if direction == 'N' and self.location > 8:
            self.location -= 8
        elif direction == 'S' and self.location < 56:
            self.location += 8
        elif direction == 'E' and self.location > 1:
            self.location -= 1
        elif direction == 'W' and self.location < 64:
            self.location += 1
        self.strength -= 1
        self.check_strength()

    def conflict(self, creature, health):
        cost = self.rng.randrange(1, 11)
        action = ask('Swim away (S) or fight (F)? ', {'S', 'F'})
        if action == 'S':
            if self.rng.random() > .5:
                print('The creature catches you!')
                self.finish()
                return
            print(f'You got away, losing {cost} strength.')
            self.strength -= cost
            if not self.check_strength():
                return
            # BASIC's successful escape searches these cells in this order.
            for target, allowed in ((self.location-1,self.location>1),
                                    (self.location+1,self.location<64),
                                    (self.location+8,self.location<56),
                                    (self.location-8,self.location>8)):
                if allowed and self.sea[target] == 0:
                    self.location = target
                    return
            self.sea[self.location] = 0
            return
        print('\nLet the battle begin!')
        while not self.ended:
            if self.rng.random() > .66:
                print('The creature hurts you...ugh!')
                self.strength -= 1
            if self.rng.random() < .34:
                print('You launch a well-timed attack.')
                health -= self.rng.randrange(1,5)
            print(f'Creature: {health}    You: {self.strength}')
            if not self.check_strength():
                return
            if health <= 0:
                print(f'You defeated {creature}!')
                self.sea[self.location] = 0
                return

    def encounter(self):
        depth = ('in the shallows' if self.location < 17 else
                 'several fathoms down' if self.location < 33 else
                 'in the murky depths' if self.location < 49 else
                 'on the ocean floor')
        print(f'\nPEARL DIVER\nYou are {depth}.\nYour strength is {self.strength}.')
        item = self.sea[self.location]
        if item in CREATURES:
            creature, health = CREATURES[item]
            print(f'You can see {creature}!')
            self.conflict(creature,health)
        elif item == 0:
            print('You can see nothing.')
        elif item == 4:
            print('Seaweed! You untangle yourself but lose 5 strength.')
            self.strength -= 5
            self.check_strength()
        elif item == 5:
            print('An oyster! You collect a pearl.')
            self.treasure += 1
            self.sea[self.location] = 0
        elif item == 6:
            print('An old chest.')
            if ask('Do you wish to open it (Y/N)? ', {'Y','N'}) == 'Y':
                if self.rng.random() > .66:
                    print('A hideous spirit leaps out and kills you!')
                    self.finish()
                else:
                    print('You found much treasure! Go back to your boat a rich diver.')
                    self.treasure = 5
        elif item == 8:
            print('An oxygen cylinder! It adds 15 to your strength.')
            self.strength += 15
            self.sea[self.location] = 0
        elif item == 9:
            print("A shoal of fish...don't worry, they are harmless.")
        elif item == 10:
            print('Your boat. You dump your treasures in the boat.')
            if self.treasure >= 5:
                self.finish(True)
            else:
                print(f'You now need {5-self.treasure} oysters.')

    def play(self):
        print('P E A R L   D I V E R')
        print('Collect five pearls (or chest treasure), then return to your boat.')
        print('Move with N/S/E/W. Q quits. Each movement attempt costs strength.')
        while not self.ended:
            self.encounter()
            if self.ended:
                break
            while True:
                direction = input('\nWhich direction (N/S/E/W, Q)? ').strip().upper()
                if direction == 'Q':
                    print('Dive ended.')
                    return
                if direction in {'N','S','E','W'}:
                    self.move(direction)
                    break
                print('No such direction. You lose 1 strength.')
                self.strength -= 1
                if not self.check_strength():
                    return

def ask(prompt, choices):
    while True:
        answer = input(prompt).strip().upper()
        if answer in choices:
            return answer
        if answer == 'Q':
            raise EOFError
        print('Choose ' + ' or '.join(sorted(choices)) + '.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, help='Reproducible random encounters')
    args = parser.parse_args()
    try:
        Game(rng=random.Random(args.seed)).play()
    except (EOFError, KeyboardInterrupt):
        print('\nDive ended.')

if __name__ == '__main__':
    main()
