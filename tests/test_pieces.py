"""Piece movement tests."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

Board4D = importlib.import_module("4d_chess.board").Board4D
pieces_module = importlib.import_module("4d_chess.pieces")
Cat = pieces_module.Cat
Knight = pieces_module.Knight
Pawn = pieces_module.Pawn
Rook = pieces_module.Rook
default_players = importlib.import_module("4d_chess.player").default_players


def test_rook_moves_along_axes() -> None:
    board = Board4D((4, 4, 4, 4))
    player = default_players()[0]
    rook = Rook(player)
    board.place_piece(rook, (1, 1, 1, 1))
    moves = rook.legal_moves(board)
    assert (0, 1, 1, 1) in moves
    assert (1, 0, 1, 1) in moves
    assert (1, 1, 3, 1) in moves
    assert (1, 1, 1, 3) in moves


def test_knight_moves_l_shape() -> None:
    board = Board4D((5, 5, 5, 5))
    player = default_players()[0]
    knight = Knight(player)
    board.place_piece(knight, (2, 2, 2, 2))
    moves = knight.legal_moves(board)
    assert (4, 3, 2, 2) in moves
    assert (0, 1, 2, 2) in moves
    assert (2, 0, 1, 2) in moves


def test_pawn_forward_and_capture() -> None:
    board = Board4D((4, 4, 4, 4))
    players = default_players()
    pawn = Pawn(players[0])
    enemy = Pawn(players[1])
    board.place_piece(pawn, (1, 1, 1, 1))
    board.place_piece(enemy, (2, 2, 1, 1))
    moves = pawn.legal_moves(board)
    assert (2, 1, 1, 1) in moves  # forward
    assert (2, 2, 1, 1) in moves  # capture


def test_cat_dimension_hop() -> None:
    board = Board4D((4, 4, 4, 4))
    player = default_players()[0]
    cat = Cat(player)
    board.place_piece(cat, (1, 2, 3, 0))
    moves = cat.legal_moves(board)
    assert (3, 2, 1, 0) in moves  # permutation of coordinates


def test_cat_linear_slip() -> None:
    board = Board4D((8, 8, 8, 8))
    player = default_players()[0]
    cat = Cat(player)
    board.place_piece(cat, (3, 3, 3, 3))
    moves = cat.legal_moves(board)
    assert (6, 5, 3, 3) in moves  # change along two axes in a single leap

