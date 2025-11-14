"""Tests for the 4D board mechanics."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

Board4D = importlib.import_module("4d_chess.board").Board4D
pieces_module = importlib.import_module("4d_chess.pieces")
Alien = pieces_module.Alien
Pawn = pieces_module.Pawn
Rook = pieces_module.Rook
default_players = importlib.import_module("4d_chess.player").default_players


@pytest.fixture
def players():
    return default_players()


def test_move_piece_and_bounds(players) -> None:
    board = Board4D((4, 4, 4, 4))
    rook = Rook(players[0])
    pawn = Pawn(players[1])
    board.place_piece(rook, (1, 1, 1, 1))
    board.place_piece(pawn, (1, 3, 1, 1))
    captured = board.move_piece((1, 1, 1, 1), (1, 3, 1, 1))
    assert captured is pawn
    assert rook.position == (1, 3, 1, 1)
    with pytest.raises(ValueError):
        board.move_piece((0, 0, 0, 0), (0, 1, 0, 0))


def test_transpose_operation(players) -> None:
    board = Board4D((2, 3, 4, 5))
    alien = Alien(players[0])
    rook = Rook(players[1])
    board.place_piece(alien, (0, 0, 0, 0))
    board.place_piece(rook, (1, 2, 3, 4))
    board.transpose((1, 0, 2, 3), alien)
    assert board.dimensions == (3, 2, 4, 5)
    assert rook.position == (2, 1, 3, 4)
    assert alien.position == (0, 0, 0, 0)


def test_reshape_axis(players) -> None:
    board = Board4D((8, 8, 8, 8))
    alien = Alien(players[0])
    rook = Rook(players[1])
    board.place_piece(alien, (0, 0, 0, 0))
    board.place_piece(rook, (3, 0, 0, 0))
    board.reshape_axis(0, 4, alien)
    assert rook.position == (6, 0, 0, 0)


def test_transformation_collision_eliminates(players) -> None:
    board = Board4D((4, 4, 4, 4))
    alien = Alien(players[0])
    piece_a = Rook(players[1])
    piece_b = Rook(players[2])
    board.place_piece(alien, (0, 0, 0, 0))
    board.place_piece(piece_a, (1, 0, 0, 0))
    board.place_piece(piece_b, (0, 1, 0, 0))

    def mapper(position):
        x, y, z, w = position
        return (0, 0, z, w)

    result = board.apply_transformation(mapper, alien)
    assert piece_a not in result.survivors.values()
    assert piece_b not in result.survivors.values()
    assert not piece_a.is_active
    assert not piece_b.is_active

