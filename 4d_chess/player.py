"""Player model for 4D chess."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Player:
    """Represents one participant in the four-dimensional chess match."""

    index: int
    identifier: str
    color: str
    forward_axis: int
    forward_direction: int

    def owns(self, piece: "Piece") -> bool:
        return piece.player is self

    @property
    def home_rank(self) -> int:
        return 0 if self.forward_direction > 0 else -1

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        return self.identifier


def default_players() -> List[Player]:
    """Return the default set of up to four players."""

    return [
        Player(index=0, identifier="Alpha", color="White", forward_axis=0, forward_direction=1),
        Player(index=1, identifier="Beta", color="Black", forward_axis=0, forward_direction=-1),
        Player(index=2, identifier="Gamma", color="Gold", forward_axis=1, forward_direction=1),
        Player(index=3, identifier="Delta", color="Azure", forward_axis=1, forward_direction=-1),
    ]


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - avoid circular at runtime
    from .pieces import Piece
