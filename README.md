# 4D Chess: Cat Scratches and Alien Layouts

A fully playable four-dimensional chess engine implemented in Python. The game
supports up to four players, standard chess pieces extended to 4D movement, and
two new pieces: the dimension-hopping **Cat** and the space-warping **Alien**.

## Table of Contents

- [Why four dimensions?](#why-four-dimensions)
- [Board model](#board-model)
- [Piece movement](#piece-movement)
  - [Standard pieces](#standard-pieces)
  - [Cat](#cat)
  - [Alien](#alien)
- [Gameplay examples](#gameplay-examples)
- [Command-line interface](#command-line-interface)
- [Installation](#installation)
- [Running the game](#running-the-game)
- [Tests](#tests)
- [Extensibility](#extensibility)
- [Deploy to GitHub](#deploy-to-github)
- [License](#license)

## Why four dimensions?

Traditional chess pieces can be generalised by adding two more spatial axes.
Instead of a single 8×8 board, the default setup works on an 8×8×8×8 hypercube.
The extra dimensions unlock new patterns of motion, simultaneous multi-axis
attacks, and novel defensive structures. The fourth dimension is a natural
playground for polymorphic movement strategies and data-driven rules.

## Board model

Coordinates are expressed as tuples `(x, y, z, w)` with zero-based indexing. The
default board size is `(8, 8, 8, 8)`. Movement logic never hardcodes these
values, so you can supply a different size when constructing a
`FourDChessGame`.

Pieces live on layers of this hypercube:

- Axes 0 and 1 (`x` and `y`) behave like the familiar ranks and files.
- Axis 2 (`z`) separates stacked battlefields.
- Axis 3 (`w`) separates player territories or staging areas.

The `Alien` piece can perform transformations that permute or reshape these
axes, affecting every other piece on the board simultaneously.

## Piece movement

Each piece class exposes a `legal_moves` method returning a set of reachable
coordinates. Movement rules are implemented through reusable strategy objects,
not hard-coded conditionals.

### Standard pieces

| Piece  | 4D interpretation |
| ------ | ----------------- |
| King   | May move one step along any combination of axes. |
| Queen  | Combines rook and bishop moves across four dimensions. |
| Rook   | Slides along a single axis in any direction. |
| Bishop | Slides diagonally using any subset of axes with consistent step
          magnitude. |
| Knight | Moves in an “L” shape: two steps along one axis, one step along a
           different axis, zero on the remaining axes. |
| Pawn   | Has a designated forward axis per player. It advances one square (or
           two on its first move) and captures by moving forward plus one step
           along any other axis. |

### Cat

The Cat is a highly mobile disruptor with two modes of travel:

1. **Dimension hop** – the Cat may permute its coordinate tuple. From
   `(1, 2, 3, 0)` it can jump directly to `(3, 2, 1, 0)` or any other permutation
   that remains on the board.
2. **Linear slip** – the Cat may leap while adjusting at most two axes in a
   single move, ignoring blocking pieces. A slip from `(3, 3, 3, 3)` to
   `(6, 5, 3, 3)` is legal because only the `x` and `y` axes change.

Whenever the Cat lands on an enemy square it **scratches** the target. Instead of
capturing it, the Cat swaps places with the victim and the scratched piece is
permanently downgraded to pawn-like movement (aligned with its owner’s forward
axis). The scratched piece keeps its name and ownership but now moves exactly as
one of that player’s pawns.

### Alien

The Alien can move like a king, but its signature ability is reshaping the board
layout. On its turn the owning player may choose to perform one of these
operations instead of a normal move:

- `transpose a b c d` – reorder the axes according to the provided permutation.
- `swapaxis i j` – swap two specific axes (a convenient shorthand for
  `transpose`).
- `moveaxis src dst` – remove the axis at `src` and reinsert it at `dst`, similar
  to `numpy.moveaxis`.
- `reshapeaxis axis new_size` – reinterpret the specified axis by treating it as
  a matrix of shape `(new_size, old_size/new_size)` and flattening it in column
  major order. This bijection scrambles coordinates without changing the board
  size.

All pieces except the Alien itself are transformed. If multiple pieces are
mapped to the same coordinate they annihilate each other. Any piece mapped onto
the Alien’s square is also eliminated.

## Gameplay examples

- A rook at `(2, 2, 2, 2)` may slide to `(7, 2, 2, 2)` or `(2, 2, 0, 2)`.
- A bishop starting at `(1, 1, 1, 1)` can attack `(4, 4, 4, 4)` in a straight
  4D diagonal.
- A knight from `(3, 3, 3, 3)` jumps to `(5, 4, 3, 3)`.
- A Cat on `(2, 0, 0, 0)` can hop to `(0, 2, 0, 0)` or slip to `(5, 1, 0, 0)`.
- An Alien performing `swapaxis 0 1` exchanges the interpretation of the first
  two axes for every other piece while remaining stationary.

## Command-line interface

Run the CLI to start an interactive match:

```bash
python -m 4d_chess.cli --players 3 --dimensions 8 8 8 8
```

Available commands:

- `show` – display a textual projection of the current board (each plane is a
  slice of the four-dimensional space).
- `status` – show the current turn and king status for each player.
- `move x,y,z,w a,b,c,d` – move a piece from the start to the destination
  coordinate.
- `alien <operation> [args]` – perform an Alien layout operation, e.g.
  `alien reshapeaxis 0 4`.
- `help` – list commands.
- `quit` – exit the game.

The CLI validates input and prints helpful error messages when an action is not
allowed.

## Installation

1. Clone or download this repository.
2. Create a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies with `pip`:

   ```bash
   pip install -e .
   ```

   The editable install reads dependencies from `pyproject.toml` (currently just
   `pytest` for the test suite).

## Running the game

Once installed, launch the CLI using one of the following commands:

```bash
python -m 4d_chess.cli
# or
python 4d_chess/cli.py
```

Use the prompts to move pieces and unleash Cat scratches or Alien operations.
The textual projection shows each `(z, w)` slice in turn so you can keep track
of the evolving hypercube.

## Tests

Run the automated test suite with `pytest`:

```bash
pytest
```

The tests cover:

- Movement rules for all major piece types, including the Cat’s dimension hop
  and linear slip.
- Cat scratch mechanics (swap and demotion).
- Alien layout operations and their turn-handling behaviour.
- Board transformation edge cases, such as collisions during reshapes.

## Extensibility

- **Custom boards** – pass a new dimension tuple into `FourDChessGame` to change
  the board size.
- **New pieces** – subclass `Piece` and provide a custom `MovementPattern`. The
  architecture keeps rules data-driven, so you can create entirely new behaviour
  without editing the core engine.
- **Alternative layouts** – modify `FourDChessGame._setup_initial_positions` to
  experiment with asymmetric setups or scenario play.

## Deploy to GitHub

Ready to publish your fork? Run these commands from the project root:

```bash
git init
git add .
git commit -m "Initial commit: 4D Chess Game with Cat & Alien pieces"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## License

Meow Meow Creative Commons, for non-commercial use. See [LICENSE.txt](LICENSE.txt)
for the full text.
