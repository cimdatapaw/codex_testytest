"""Board management for 4D chess."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from .pieces import Piece

Coordinate = Tuple[int, int, int, int]


@dataclass
class TransformationResult:
    """Represents the outcome of applying an Alien transformation."""

    survivors: Dict[Coordinate, Piece]
    casualties: List[Piece]


class Board4D:
    """Model of a four-dimensional chess board."""

    def __init__(self, dimensions: Sequence[int]) -> None:
        if len(dimensions) != 4:
            raise ValueError("Board must have exactly four dimensions")
        self.dimensions: Tuple[int, int, int, int] = tuple(dimensions)  # type: ignore[assignment]
        self._pieces: Dict[Coordinate, Piece] = {}

    def is_within_bounds(self, position: Coordinate) -> bool:
        return all(0 <= coordinate < limit for coordinate, limit in zip(position, self.dimensions))

    def place_piece(self, piece: Piece, position: Coordinate) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is outside of the board")
        if position in self._pieces:
            raise ValueError(f"Position {position} already occupied")
        self._pieces[position] = piece
        piece.position = position

    def remove_piece(self, position: Coordinate) -> Optional[Piece]:
        piece = self._pieces.pop(position, None)
        if piece is not None:
            piece.position = None
            piece.is_active = False
        return piece

    def move_piece(self, start: Coordinate, end: Coordinate) -> Optional[Piece]:
        if start not in self._pieces:
            raise ValueError("No piece at start position")
        piece = self._pieces[start]
        captured = self._pieces.pop(end, None)
        self._pieces.pop(start)
        self._pieces[end] = piece
        piece.position = end
        piece.has_moved = True
        if captured is not None:
            captured.position = None
            captured.is_active = False
        return captured

    def swap_with_cat(self, start: Coordinate, end: Coordinate, cat: Piece, target: Piece) -> None:
        """Special movement helper used when a cat scratches another piece."""

        if self._pieces.get(start) is not cat:
            raise ValueError("Cat must occupy the start coordinate")
        if self._pieces.get(end) is not target:
            raise ValueError("Target must occupy the destination coordinate")
        self._pieces[end] = cat
        cat.position = end
        cat.has_moved = True
        self._pieces[start] = target
        target.position = start
        target.has_moved = True

    def get_piece(self, position: Coordinate) -> Optional[Piece]:
        return self._pieces.get(position)

    def pieces(self) -> Iterator[Tuple[Coordinate, Piece]]:
        yield from self._pieces.items()

    def locate_pieces(self, predicate: Callable[[Piece], bool]) -> List[Piece]:
        return [piece for piece in self._pieces.values() if predicate(piece)]

    def apply_transformation(self, mapping: Callable[[Coordinate], Coordinate], preserve: Piece) -> TransformationResult:
        """Apply a coordinate mapping to all pieces except *preserve*.

        When two pieces map to the same coordinate they annihilate each other.
        """

        updated: Dict[Coordinate, Piece] = {}
        casualties: List[Piece] = []
        preserve_position = preserve.position
        for position, piece in list(self._pieces.items()):
            if piece is preserve:
                updated[position] = piece
                continue
            new_position = mapping(position)
            if not self.is_within_bounds(new_position):
                casualties.append(piece)
                self._pieces.pop(position)
                piece.position = None
                piece.is_active = False
                continue
            if preserve_position is not None and new_position == preserve_position:
                casualties.append(piece)
                self._pieces.pop(position, None)
                piece.position = None
                piece.is_active = False
                continue
            existing = updated.get(new_position)
            if existing is not None and existing is not preserve:
                casualties.extend([existing, piece])
                updated.pop(new_position)
                self._pieces.pop(position, None)
                existing.position = None
                existing.is_active = False
                piece.position = None
                piece.is_active = False
                continue
            updated[new_position] = piece
            self._pieces.pop(position, None)
            piece.position = new_position
        self._pieces = updated
        return TransformationResult(updated, casualties)

    def transpose(self, order: Sequence[int], preserve: Piece) -> TransformationResult:
        if sorted(order) != [0, 1, 2, 3]:
            raise ValueError("Order must be a permutation of axes 0..3")

        def mapper(position: Coordinate) -> Coordinate:
            return tuple(position[index] for index in order)  # type: ignore[return-value]

        self.dimensions = tuple(self.dimensions[index] for index in order)  # type: ignore[assignment]
        return self.apply_transformation(mapper, preserve)

    def swap_axes(self, axis_a: int, axis_b: int, preserve: Piece) -> TransformationResult:
        order = list(range(4))
        order[axis_a], order[axis_b] = order[axis_b], order[axis_a]
        return self.transpose(order, preserve)

    def move_axis(self, source: int, destination: int, preserve: Piece) -> TransformationResult:
        order = list(range(4))
        axis = order.pop(source)
        order.insert(destination, axis)

        def mapper(position: Coordinate) -> Coordinate:
            return tuple(position[index] for index in order)  # type: ignore[return-value]

        self.dimensions = tuple(self.dimensions[index] for index in order)  # type: ignore[assignment]
        return self.apply_transformation(mapper, preserve)

    def reshape_axis(self, axis: int, new_size: int, preserve: Piece) -> TransformationResult:
        if new_size <= 0:
            raise ValueError("New size must be positive")
        old_size = self.dimensions[axis]
        if old_size % new_size != 0:
            raise ValueError("New size must divide the old size")
        block = old_size // new_size

        def mapper(position: Coordinate) -> Coordinate:
            components = list(position)
            value = components[axis]
            new_value = (value % new_size) * block + (value // new_size)
            components[axis] = new_value
            return tuple(components)  # type: ignore[return-value]

        return self.apply_transformation(mapper, preserve)

    def serialize_projection(self, axis_order: Sequence[int] = (0, 1, 2, 3)) -> List[str]:
        """Return a textual representation of the board for CLI display."""

        lines: List[str] = []
        order = list(axis_order)
        plane_axes = order[:2]
        depth_axes = order[2:]
        dims = [self.dimensions[idx] for idx in order]
        for depth_coords in self._iter_depth_coordinates(depth_axes, dims[2:]):
            header = "Depth " + ",".join(f"{axis}={value}" for axis, value in zip(depth_axes, depth_coords))
            lines.append(header)
            for row in range(dims[1]):
                row_cells: List[str] = []
                for col in range(dims[0]):
                    position_components = [0, 0, 0, 0]
                    position_components[plane_axes[0]] = col
                    position_components[plane_axes[1]] = row
                    for axis, value in zip(depth_axes, depth_coords):
                        position_components[axis] = value
                    coord = tuple(position_components)  # type: ignore[assignment]
                    piece = self.get_piece(coord)
                    if piece is None:
                        row_cells.append(".")
                    else:
                        row_cells.append(piece.short_name.lower() if piece.player.index % 2 else piece.short_name)
                lines.append("".join(row_cells))
            lines.append("")
        return lines

    def _iter_depth_coordinates(self, axes: Sequence[int], dims: Sequence[int]) -> Iterable[Tuple[int, ...]]:
        if not axes:
            yield ()
            return
        axis = axes[0]
        size = dims[0]
        for value in range(size):
            for remainder in self._iter_depth_coordinates(axes[1:], dims[1:]):
                yield (value,) + remainder

