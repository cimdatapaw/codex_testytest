"""Integration tests for game orchestration."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

Board4D = importlib.import_module("4d_chess.board").Board4D
FourDChessGame = importlib.import_module("4d_chess.game").FourDChessGame
pieces_module = importlib.import_module("4d_chess.pieces")
Alien = pieces_module.Alien
Cat = pieces_module.Cat
King = pieces_module.King
Rook = pieces_module.Rook


def prepare_custom_game(player_count: int = 2):
    game = FourDChessGame(player_count=player_count)
    game.board = Board4D((5, 5, 5, 5))
    game._player_pieces = {player: [] for player in game.players}
    return game


def test_cat_scratch_transforms_piece() -> None:
    game = prepare_custom_game()
    players = game.players
    cat = Cat(players[0])
    victim = Rook(players[1])
    game.board.place_piece(cat, (2, 0, 0, 0))
    game.board.place_piece(victim, (3, 0, 0, 0))
    game._player_pieces[players[0]].append(cat)
    game._player_pieces[players[1]].append(victim)

    game.move((2, 0, 0, 0), (3, 0, 0, 0))

    assert cat.position == (3, 0, 0, 0)
    assert victim.position == (2, 0, 0, 0)
    # Victim now behaves like a pawn moving backwards along axis 0
    assert (1, 0, 0, 0) in victim.legal_moves(game.board)
    assert game.current_player is players[1]


def test_alien_swapaxis_advances_turn() -> None:
    game = prepare_custom_game()
    players = game.players
    alien = Alien(players[0])
    ally = Rook(players[0])
    game.board.place_piece(alien, (0, 2, 0, 0))
    game.board.place_piece(ally, (1, 0, 0, 0))
    game._player_pieces[players[0]].extend([alien, ally])

    game.perform_alien_operation(players[0], "swapaxis", 0, 1)

    assert ally.position == (0, 1, 0, 0)
    assert game.current_player is players[1]


def test_winner_detected_after_king_removed() -> None:
    game = prepare_custom_game()
    players = game.players
    king_a = King(players[0])
    king_b = King(players[1])
    game.board.place_piece(king_a, (0, 0, 0, 0))
    game.board.place_piece(king_b, (4, 4, 4, 4))
    game._player_pieces[players[0]].append(king_a)
    game._player_pieces[players[1]].append(king_b)

    game.board.remove_piece((4, 4, 4, 4))
    game._player_pieces[players[1]].remove(king_b)
    game._update_winner()

    assert game.winner is players[0]

