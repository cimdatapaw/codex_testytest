"""Game orchestration for 4D chess."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .board import Board4D, Coordinate
from .pieces import (
    Alien,
    Bishop,
    Cat,
    King,
    Knight,
    Pawn,
    Piece,
    Queen,
    Rook,
)
from .player import Player, default_players


class FourDChessGame:
    """Coordinate the 4D chess gameplay including turns and rules."""

    def __init__(self, player_count: int = 2, dimensions: Sequence[int] = (8, 8, 8, 8)) -> None:
        if player_count < 2 or player_count > 4:
            raise ValueError("Player count must be between 2 and 4")
        self.players: List[Player] = default_players()[:player_count]
        self.board = Board4D(dimensions)
        self.turn_index: int = 0
        self.winner: Optional[Player] = None
        self._player_pieces: Dict[Player, List[Piece]] = {player: [] for player in self.players}
        self._setup_initial_positions()

    @property
    def current_player(self) -> Player:
        return self.players[self.turn_index]

    def _setup_initial_positions(self) -> None:
        z_positions = [0, 0, self.board.dimensions[2] - 1, self.board.dimensions[2] - 1]
        w_positions = [0, self.board.dimensions[3] - 1, 0, self.board.dimensions[3] - 1]
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for player in self.players:
            base_z = z_positions[player.index % len(z_positions)]
            base_w = w_positions[player.index % len(w_positions)]
            orientation_axis = player.forward_axis
            rank_axis = 1 if orientation_axis == 0 else 0
            primary_rank = 0 if player.forward_direction > 0 else self.board.dimensions[orientation_axis] - 1
            pawn_rank = primary_rank + player.forward_direction
            for file_index, piece_type in enumerate(piece_order):
                coord = [0, 0, base_z, base_w]
                coord[orientation_axis] = primary_rank
                coord[rank_axis] = file_index
                piece = piece_type(player)
                self._register_piece(piece, tuple(coord))
            for file_index in range(self.board.dimensions[rank_axis]):
                coord = [0, 0, base_z, base_w]
                coord[orientation_axis] = pawn_rank
                coord[rank_axis] = file_index
                pawn = Pawn(player)
                self._register_piece(pawn, tuple(coord))
            # Cat positioned adjacent along the z-axis near the queen
            queen_file = 3
            cat_coord = [0, 0, base_z, base_w]
            cat_coord[orientation_axis] = primary_rank
            cat_coord[rank_axis] = queen_file
            cat_coord[2] = self._offset_axis(base_z, self.board.dimensions[2])
            cat = Cat(player)
            self._register_piece(cat, tuple(cat_coord))
            # Alien anchored near the king along the w-axis
            king_file = 4
            alien_coord = [0, 0, base_z, base_w]
            alien_coord[orientation_axis] = primary_rank
            alien_coord[rank_axis] = king_file
            alien_coord[3] = self._offset_axis(base_w, self.board.dimensions[3])
            alien = Alien(player)
            self._register_piece(alien, tuple(alien_coord))

    def _offset_axis(self, base: int, limit: int) -> int:
        if base + 1 < limit:
            return base + 1
        if base - 1 >= 0:
            return base - 1
        return base

    def _register_piece(self, piece: Piece, position: Coordinate) -> None:
        self.board.place_piece(piece, position)
        self._player_pieces[piece.player].append(piece)

    def legal_moves_from(self, position: Coordinate) -> List[Coordinate]:
        piece = self.board.get_piece(position)
        if piece is None:
            return []
        return sorted(piece.legal_moves(self.board))

    def move(self, start: Coordinate, end: Coordinate) -> None:
        if self.winner is not None:
            raise RuntimeError("Game already finished")
        piece = self.board.get_piece(start)
        if piece is None:
            raise ValueError("No piece at starting coordinate")
        if piece.player is not self.current_player:
            raise ValueError("It is not this player's turn")
        legal = piece.legal_moves(self.board)
        if end not in legal:
            raise ValueError("Illegal move for the selected piece")
        destination_piece = self.board.get_piece(end)
        if isinstance(piece, Cat) and destination_piece is not None and destination_piece.player != piece.player:
            piece.scratch(destination_piece)
            self.board.swap_with_cat(start, end, piece, destination_piece)
        else:
            captured = self.board.move_piece(start, end)
            if captured is not None:
                self._player_pieces[captured.player].remove(captured)
        self._advance_turn()
        self._update_winner()

    def _advance_turn(self) -> None:
        self.turn_index = (self.turn_index + 1) % len(self.players)

    def _update_winner(self) -> None:
        alive_players = [player for player in self.players if self._king_alive(player)]
        if len(alive_players) == 1:
            self.winner = alive_players[0]

    def _king_alive(self, player: Player) -> bool:
        for piece in self._player_pieces[player]:
            if isinstance(piece, King) and piece.is_active:
                return True
        return False

    def find_alien(self, player: Player) -> Alien:
        for piece in self._player_pieces[player]:
            if isinstance(piece, Alien) and piece.is_active:
                return piece
        raise ValueError("Player does not have an active Alien")

    def perform_alien_operation(self, player: Player, operation: str, *args: int) -> None:
        if self.current_player is not player:
            raise ValueError("It is not this player's turn")
        alien = self.find_alien(player)
        operation = operation.lower()
        if operation == "transpose":
            if len(args) != 4:
                raise ValueError("transpose requires four axis indices")
            self.board.transpose(args, alien)
        elif operation == "swapaxis":
            if len(args) != 2:
                raise ValueError("swapaxis requires two axis indices")
            self.board.swap_axes(args[0], args[1], alien)
        elif operation == "moveaxis":
            if len(args) != 2:
                raise ValueError("moveaxis requires source and destination")
            self.board.move_axis(args[0], args[1], alien)
        elif operation == "reshapeaxis":
            if len(args) != 2:
                raise ValueError("reshapeaxis requires axis and new size")
            self.board.reshape_axis(args[0], args[1], alien)
        else:
            raise ValueError(f"Unknown alien operation: {operation}")
        self._advance_turn()
        self._update_winner()

    def pieces_for_player(self, player: Player) -> Iterable[Piece]:
        return [piece for piece in self._player_pieces[player] if piece.is_active]

    def status_report(self) -> str:
        report_lines = [f"Turn: {self.current_player.identifier}"]
        for player in self.players:
            king_state = "alive" if self._king_alive(player) else "captured"
            report_lines.append(f"{player.identifier} king: {king_state}")
        if self.winner is not None:
            report_lines.append(f"Winner: {self.winner.identifier}")
        return "\n".join(report_lines)

