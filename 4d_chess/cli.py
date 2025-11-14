"""Command-line interface for the 4D chess game."""
from __future__ import annotations

import argparse
import sys
from typing import Iterable, Sequence

from .game import FourDChessGame


def parse_coordinate(text: str) -> Sequence[int]:
    parts = text.replace("(", "").replace(")", "").split(",")
    if len(parts) != 4:
        raise ValueError("Coordinates must have four comma-separated values")
    return [int(part.strip()) for part in parts]


def format_projection(lines: Iterable[str]) -> str:
    return "\n".join(lines)


def run_game(players: int, dimensions: Sequence[int]) -> None:
    game = FourDChessGame(player_count=players, dimensions=dimensions)
    print("Welcome to 4D Chess! Type 'help' for a list of commands.")
    while True:
        if game.winner is not None:
            print(game.status_report())
            break
        try:
            raw = input(f"[{game.current_player.identifier}] > ").strip()
        except EOFError:
            print()
            break
        if not raw:
            continue
        if raw.lower() in {"quit", "exit"}:
            print("Exiting game.")
            break
        if raw.lower() == "help":
            print("""
Commands:
  show                          Display a projection of the board.
  status                        Display the current game status.
  move x,y,z,w a,b,c,d          Move from start to end coordinate.
  alien <op> [args]             Perform an alien layout operation. Examples:
                                alien transpose 0 1 2 3
                                alien swapaxis 0 2
                                alien moveaxis 3 0
                                alien reshapeaxis 0 4
  help                          Show this message.
  quit                          Exit the game.
""")
            continue
        if raw.lower() == "show":
            print(format_projection(game.board.serialize_projection()))
            continue
        if raw.lower() == "status":
            print(game.status_report())
            continue
        tokens = raw.split()
        if tokens[0].lower() == "move" and len(tokens) == 3:
            try:
                start = tuple(parse_coordinate(tokens[1]))
                end = tuple(parse_coordinate(tokens[2]))
                game.move(start, end)
            except Exception as exc:  # pragma: no cover - CLI convenience
                print(f"Error: {exc}")
            continue
        if tokens[0].lower() == "alien":
            try:
                op = tokens[1]
                args = [int(value) for value in tokens[2:]]
                game.perform_alien_operation(game.current_player, op, *args)
            except Exception as exc:  # pragma: no cover - CLI convenience
                print(f"Error: {exc}")
            continue
        print("Unknown command. Type 'help' for assistance.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play a game of 4D chess")
    parser.add_argument("--players", type=int, default=2, help="Number of players (2-4)")
    parser.add_argument(
        "--dimensions",
        type=int,
        nargs=4,
        default=(8, 8, 8, 8),
        help="Board dimensions as four integers",
    )
    args = parser.parse_args(argv)
    try:
        run_game(args.players, args.dimensions)
    except Exception as exc:  # pragma: no cover - CLI convenience
        print(f"Fatal error: {exc}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
