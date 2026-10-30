# pearl-diver
Python version of a text based game of the Pearl diver game which was originally printed as BASIC code in the book Adventures for the ZX Spectrum

No external packages are required. Requires Python 3.9+.

## Run

    python pearl_diver.py

On Windows, `py pearl_diver.py` also works. For reproducible randomness:

    python pearl_diver.py --seed 42

Collect five oyster pearls, or find treasure in the chest, then return to the
boat. Type N, S, E, or W to move; type Q to quit. Combat offers F (fight) or
S (swim away). Oxygen cylinders restore 15 strength. Seaweed costs 5.
A failed escape is fatal; combat proceeds automatically, as in the original.

## Translation choices

The original map, start location (3), strength (90), creature health, random
thresholds, and encounter rules are retained. This includes some unusual rules:
E decreases the location number, W increases it, and either can cross a row
boundary. A blocked movement still costs strength. The 64 DATA values load into
cells 2–65; cell 1 is empty and cell 65 is unreachable under the original
movement rules. The boat is at cell 17. Escaping searches for an empty neighboring
cell in the original order; if none exists, the current creature is removed.
The chest remains available after opening, and treasure is set to 5 on success.

Deliberate corrections:
- BASIC line 240 sends exhaustion to the victory routine. Python makes it defeat.
- BASIC line 1320 likewise sends a lethal spirit encounter to victory. Python
  makes it defeat.
- Strength reaching zero after seaweed, escape, or invalid input causes immediate
  defeat instead of allowing another action.
- Neighbor bounds are checked before array access, avoiding BASIC's possible
  out-of-range A(0) access during escape.
- Only Y opens a chest; the original treats any response except uppercase N as yes.
- Input accepts lowercase and surrounding whitespace. Q and clean EOF/interrupt
  handling are additions.

Spectrum colors, flashing, sound, screen coordinates, and pauses are represented
by plain terminal text or omitted. This is a terminal game, not a tape emulator.
`original_basic.txt` contains the extracted listing for comparison; token spacing
is expanded and Spectrum control bytes, if present, appear in hexadecimal braces.
