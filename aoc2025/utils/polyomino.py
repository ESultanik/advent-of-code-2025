from dataclasses import dataclass
from typing import Self

@dataclass(frozen=True, slots=True, unsafe_hash=True)
class Coord:
    """An immutable 2D coordinate."""

    x: int
    y: int

    def __add__(self, other: Self) -> Self:
        return Coord(self.x + other.x, self.y + other.y)

    def rotate_cw(self) -> Self:
        """Rotate 90° clockwise around origin."""
        return Coord(-self.y, self.x)

    def flip_horizontal(self) -> Self:
        """Flip horizontally (mirror over Y axis)."""
        return Coord(-self.x, self.y)


@dataclass(frozen=True)
class Polyomino:
    """
    An immutable polyomino shape represented as a frozenset of coordinates.
    Normalized so minimum x and y are both 0.
    """

    cells: frozenset[Coord]
    shape_id: int = -1
    instance_id: int = 0  # For multiple copies of same shape

    @classmethod
    def from_pattern(cls, pattern: str, shape_id: int = -1, coord_char: str = '#') -> Self:
        """Parse a polyomino from a visual pattern string."""
        cells: set[Coord] = set()
        for y, line in enumerate(pattern.strip().split("\n")):
            for x, char in enumerate(line):
                if char == coord_char:
                    cells.add(Coord(x, y))
        return cls(cells=frozenset(cells), shape_id=shape_id)._normalize()

    def _normalize(self) -> Self:
        """Normalize so minimum x and y are 0."""
        if not self.cells:
            return self
        min_x = min(c.x for c in self.cells)
        min_y = min(c.y for c in self.cells)
        offset = Coord(-min_x, -min_y)
        return Polyomino(
            cells=frozenset(c + offset for c in self.cells),
            shape_id=self.shape_id,
            instance_id=self.instance_id,
        )

    def rotate_cw(self) -> Self:
        """Return a new polyomino rotated 90° clockwise."""
        return Polyomino(
            cells=frozenset(c.rotate_cw() for c in self.cells),
            shape_id=self.shape_id,
            instance_id=self.instance_id,
        )._normalize()

    def flip_horizontal(self) -> Self:
        """Return a new polyomino flipped horizontally."""
        return Polyomino(
            cells=frozenset(c.flip_horizontal() for c in self.cells),
            shape_id=self.shape_id,
            instance_id=self.instance_id,
        )._normalize()

    def all_orientations(self) -> set[Self]:
        """Generate all unique orientations (rotations and reflections)."""
        orientations: set[Polyomino] = set()
        current = self

        # 4 rotations
        for _ in range(4):
            orientations.add(current)
            current = current.rotate_cw()

        # Flip and 4 more rotations
        current = self.flip_horizontal()
        for _ in range(4):
            orientations.add(current)
            current = current.rotate_cw()

        return orientations  # type: ignore[return-value]

    def translate(self, offset: Coord) -> Self:
        """Return a new polyomino translated by offset."""
        return Polyomino(
            cells=frozenset(c + offset for c in self.cells),
            shape_id=self.shape_id,
            instance_id=self.instance_id,
        )

    def with_instance_id(self, instance_id: int) -> Self:
        """Return a copy with a different instance ID."""
        return Polyomino(
            cells=self.cells, shape_id=self.shape_id, instance_id=instance_id
        )

    @property
    def width(self) -> int:
        return max(c.x for c in self.cells) + 1 if self.cells else 0

    @property
    def height(self) -> int:
        return max(c.y for c in self.cells) + 1 if self.cells else 0

    @property
    def area(self) -> int:
        return len(self.cells)

    def __hash__(self) -> int:
        return hash((self.cells, self.shape_id, self.instance_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Polyomino):
            return NotImplemented
        return (
            self.cells == other.cells
            and self.shape_id == other.shape_id
            and self.instance_id == other.instance_id
        )
