"""Piece definitions for 4D Chess."""
from __future__ import annotations

from typing import List, Optional, Sequence, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported only for type checking
    from .board import Board4D
    from .player import Player

Coordinate = Tuple[int, int, int, int]


class MovementPattern:
    """Strategy object describing how a piece can move on the board."""

    def legal_moves(self, board: "Board4D", piece: "Piece", position: Coordinate) -> Set[Coordinate]:
        """Return the set of legal destination coordinates for the piece.

        Subclasses must implement this method.
        """

        raise NotImplementedError


class SlidingMovement(MovementPattern):
    """Movement pattern for pieces that slide along a set of directions."""

    def __init__(self, directions: Sequence[Coordinate], max_distance: Optional[int] = None) -> None:
        self.directions = directions
        self.max_distance = max_distance

    def legal_moves(self, board: "Board4D", piece: "Piece", position: Coordinate) -> Set[Coordinate]:
        moves: Set[Coordinate] = set()
        for direction in self.directions:
            current = position
            distance = 0
            while True:
                distance += 1
                if self.max_distance is not None and distance > self.max_distance:
                    break
                current = tuple(coord + step for coord, step in zip(current, direction))  # type: ignore[arg-type]
                if not board.is_within_bounds(current):
                    break
                occupant = board.get_piece(current)
                if occupant is None:
                    moves.add(current)
                    continue
                if occupant.player != piece.player:
                    moves.add(current)
                break
        return moves


class KnightMovement(MovementPattern):
    """Movement pattern describing the 4D knight."""

    def __init__(self, offsets: Sequence[Coordinate]) -> None:
        self.offsets = offsets

    def legal_moves(self, board: "Board4D", piece: "Piece", position: Coordinate) -> Set[Coordinate]:
        moves: Set[Coordinate] = set()
        for offset in self.offsets:
            target = tuple(coord + step for coord, step in zip(position, offset))  # type: ignore[arg-type]
            if not board.is_within_bounds(target):
                continue
            occupant = board.get_piece(target)
            if occupant is None or occupant.player != piece.player:
                moves.add(target)
        return moves


class PawnMovement(MovementPattern):
    """Movement pattern for 4D pawns."""

    def __init__(self, forward_axis: int, forward_direction: int) -> None:
        self.forward_axis = forward_axis
        self.forward_direction = forward_direction

    def legal_moves(self, board: "Board4D", piece: "Piece", position: Coordinate) -> Set[Coordinate]:
        moves: Set[Coordinate] = set()
        axis = self.forward_axis
        direction = self.forward_direction
        forward_step = list(position)
        forward_step[axis] += direction
        forward_coord: Coordinate = tuple(forward_step)  # type: ignore[assignment]
        if board.is_within_bounds(forward_coord) and board.get_piece(forward_coord) is None:
            moves.add(forward_coord)
            if not piece.has_moved:
                double_step = list(forward_coord)
                double_step[axis] += direction
                double_coord: Coordinate = tuple(double_step)  # type: ignore[assignment]
                if board.is_within_bounds(double_coord) and board.get_piece(double_coord) is None:
                    moves.add(double_coord)
        # captures: diagonally forward in any of the remaining axes
        for capture_axis in range(4):
            if capture_axis == axis:
                continue
            for capture_direction in (-1, 1):
                capture_step = list(position)
                capture_step[axis] += direction
                capture_step[capture_axis] += capture_direction
                capture_coord: Coordinate = tuple(capture_step)  # type: ignore[assignment]
                if not board.is_within_bounds(capture_coord):
                    continue
                occupant = board.get_piece(capture_coord)
                if occupant is not None and occupant.player != piece.player:
                    moves.add(capture_coord)
        return moves


class CatMovement(MovementPattern):
    """Movement pattern for the Cat piece."""

    def legal_moves(self, board: "Board4D", piece: "Piece", position: Coordinate) -> Set[Coordinate]:
        moves: Set[Coordinate] = set()
        # Dimension hop: permutations of coordinates
        seen: Set[Coordinate] = set()
        coords = list(position)
        def permute(current: List[int], idx: int) -> None:
            if idx == len(current):
                permuted = tuple(current)
                if permuted != position and permuted not in seen and board.is_within_bounds(permuted):
                    occupant = board.get_piece(permuted)
                    if occupant is None or occupant.player != piece.player:
                        moves.add(permuted)
                    seen.add(permuted)
                return
            for swap_idx in range(idx, len(current)):
                current[idx], current[swap_idx] = current[swap_idx], current[idx]
                permute(current, idx + 1)
                current[idx], current[swap_idx] = current[swap_idx], current[idx]
        permute(coords.copy(), 0)
        # Linear slip: change along up to two axes in a single leap
        for axis_a in range(4):
            for axis_b in range(axis_a, 4):
                for delta_a in range(-board.dimensions[axis_a] + 1, board.dimensions[axis_a]):
                    for delta_b in range(-board.dimensions[axis_b] + 1, board.dimensions[axis_b]):
                        if delta_a == 0 and delta_b == 0:
                            continue
                        if axis_a == axis_b and delta_b != 0:
                            continue  # handled by delta_a already
                        offset = [0, 0, 0, 0]
                        offset[axis_a] = delta_a
                        if axis_b != axis_a:
                            offset[axis_b] = delta_b
                        target = tuple(coord + step for coord, step in zip(position, offset))  # type: ignore[arg-type]
                        if not board.is_within_bounds(target):
                            continue
                        occupant = board.get_piece(target)
                        if occupant is None or occupant.player != piece.player:
                            moves.add(target)
        return moves


class KingMovement(SlidingMovement):
    """King movement limited to distance one in any direction."""

    def __init__(self) -> None:
        directions = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for dw in (-1, 0, 1):
                        if dx == dy == dz == dw == 0:
                            continue
                        directions.append((dx, dy, dz, dw))
        super().__init__(directions, max_distance=1)


class Piece:
    """Base class for any piece placed on the board."""

    name: str = "Piece"
    short_name: str = "?"

    def __init__(self, player: "Player", movement: MovementPattern) -> None:
        self.player = player
        self._movement = movement
        self.position: Optional[Coordinate] = None
        self.has_moved: bool = False
        self.is_active: bool = True

    def legal_moves(self, board: "Board4D") -> Set[Coordinate]:
        if self.position is None:
            return set()
        return self._movement.legal_moves(board, self, self.position)

    def set_movement(self, movement: MovementPattern) -> None:
        """Replace the movement strategy used by the piece."""

        self._movement = movement

    def describe(self) -> str:
        return f"{self.player.identifier} {self.name}"

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"{self.player.identifier}:{self.short_name}@{self.position}"


class Rook(Piece):
    name = "Rook"
    short_name = "R"

    def __init__(self, player: "Player") -> None:
        directions: List[Coordinate] = []
        for axis in range(4):
            for sign in (-1, 1):
                step = [0, 0, 0, 0]
                step[axis] = sign
                directions.append(tuple(step))
        super().__init__(player, SlidingMovement(directions))


class Bishop(Piece):
    name = "Bishop"
    short_name = "B"

    def __init__(self, player: "Player") -> None:
        directions: List[Coordinate] = []
        for dx in (-1, 1):
            for dy in (-1, 1):
                for dz in (-1, 1):
                    for dw in (-1, 1):
                        if dx == dy == dz == dw == 0:
                            continue
                        directions.append((dx, dy, dz, dw))
        super().__init__(player, SlidingMovement(directions))


class Queen(Piece):
    name = "Queen"
    short_name = "Q"

    def __init__(self, player: "Player") -> None:
        directions: List[Coordinate] = []
        basis_vectors: List[Coordinate] = []
        for axis in range(4):
            for sign in (-1, 1):
                step = [0, 0, 0, 0]
                step[axis] = sign
                basis_vectors.append(tuple(step))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for dw in (-1, 0, 1):
                        if dx == dy == dz == dw == 0:
                            continue
                        if abs(dx) + abs(dy) + abs(dz) + abs(dw) == 1:
                            continue  # already covered by rook directions
                        directions.append((dx, dy, dz, dw))
        directions.extend(basis_vectors)
        super().__init__(player, SlidingMovement(directions))


class Knight(Piece):
    name = "Knight"
    short_name = "N"

    def __init__(self, player: "Player") -> None:
        offsets: List[Coordinate] = []
        axes = range(4)
        for long_axis in axes:
            for short_axis in axes:
                if short_axis == long_axis:
                    continue
                for long_step in (-2, 2):
                    for short_step in (-1, 1):
                        vector = [0, 0, 0, 0]
                        vector[long_axis] = long_step
                        vector[short_axis] = short_step
                        offsets.append(tuple(vector))
        super().__init__(player, KnightMovement(offsets))


class King(Piece):
    name = "King"
    short_name = "K"

    def __init__(self, player: "Player") -> None:
        super().__init__(player, KingMovement())


class Pawn(Piece):
    name = "Pawn"
    short_name = "P"

    def __init__(self, player: "Player") -> None:
        super().__init__(player, PawnMovement(player.forward_axis, player.forward_direction))


class Cat(Piece):
    name = "Cat"
    short_name = "C"

    def __init__(self, player: "Player") -> None:
        super().__init__(player, CatMovement())

    def scratch(self, target: Piece) -> None:
        """Transform the target piece into a pawn-like mover."""

        target.set_movement(PawnMovement(target.player.forward_axis, target.player.forward_direction))


class Alien(Piece):
    name = "Alien"
    short_name = "A"

    def __init__(self, player: "Player") -> None:
        super().__init__(player, KingMovement())

