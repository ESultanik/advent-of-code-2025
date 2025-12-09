"""
--- Day 9: Movie Theater ---
You slide down the firepole in the corner of the playground and land in the North Pole base movie theater!

The movie theater has a big tile floor with an interesting pattern. Elves here are redecorating the theater by switching out some of the square tiles in the big grid they form. Some of the tiles are red; the Elves would like to find the largest rectangle that uses red tiles for two of its opposite corners. They even have a list of where the red tiles are located in the grid (your puzzle input).

For example:

7,1
11,1
11,7
9,7
9,5
2,5
2,3
7,3
Showing red tiles as # and other tiles as ., the above arrangement of red tiles would look like this:

..............
.......#...#..
..............
..#....#......
..............
..#......#....
..............
.........#.#..
..............
You can choose any two red tiles as the opposite corners of your rectangle; your goal is to find the largest rectangle possible.

For example, you could make a rectangle (shown as O) with an area of 24 between 2,5 and 9,7:

..............
.......#...#..
..............
..#....#......
..............
..OOOOOOOO....
..OOOOOOOO....
..OOOOOOOO.#..
..............
Or, you could make a rectangle with area 35 between 7,1 and 11,7:

..............
.......OOOOO..
.......OOOOO..
..#....OOOOO..
.......OOOOO..
..#....OOOOO..
.......OOOOO..
.......OOOOO..
..............
You could even make a thin rectangle with an area of only 6 between 7,3 and 2,3:

..............
.......#...#..
..............
..OOOOOO......
..............
..#......#....
..............
.........#.#..
..............
Ultimately, the largest rectangle you can make in this example has area 50. One way to do this is between 2,5 and 11,1:

..............
..OOOOOOOOOO..
..OOOOOOOOOO..
..OOOOOOOOOO..
..OOOOOOOOOO..
..OOOOOOOOOO..
..............
.........#.#..
..............
Using two red tiles as opposite corners, what is the largest area of any rectangle you can make?
"""

from dataclasses import dataclass
import heapq
from itertools import combinations
from typing import Iterator, Self, TypeVar

from . import challenge, example


@dataclass(frozen=True, unsafe_hash=True)
class Point2D:
    x: int
    y: int

    def __lt__(self, other: Self) -> Self:
        return self.x < other.x or (self.x == other.x and self.y < other.y)

    def manhattan_distance(self, other: Self) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def rectangle_area(self, other: Self) -> int:
        return abs(self.x - other.x + 1) * abs(self.y - other.y + 1)

    def __str__(self):
        return f"({self.x}, {self.y})"


T = TypeVar("T")


def smallest(heap: list[T]) -> Iterator[T]:
    first = True
    first_value: T | None = None
    while heap:
        s = heapq.heappop(heap)
        if not first and first_value < s:
            break
        yield s
        first_value = s
        first = False


@example("""\
7,1
11,1
11,7
9,7
9,5
2,5
2,3
7,3
""", result=50)
@challenge(day=9)
def largest_area(lines: list[str]) -> int:
    points: list[tuple[int, int]] = [
        Point2D(*(int(n) for n in line.split(',')))
        for line in lines
        if line.strip()
    ]
    areas = [
        (p1.rectangle_area(p2), p1, p2)
        for p1, p2 in combinations(points, 2)
    ]

    return next(iter(heapq.nlargest(
        1,
        (
            p1.rectangle_area(p2)
            for p1, p2 in combinations(points, 2)
        )
    )))
