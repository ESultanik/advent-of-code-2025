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
class RectilinearPolygon:
    points: tuple[Point2D, ...]

    def __contains__(self, point: Point2D | RectilinearPolygon) -> bool:
        if isinstance(point, RectilinearPolygon):
            return all(p in self for p in point.points)

        n = len(self.points)
        inside = False

        p1 = self.points[0]
        for i in range(1, n + 1):
            p2 = self.points[i % n]

            # Check if point is on the edge (for rectilinear polygons)
            if p1.x == p2.x == point.x:  # Vertical edge
                if min(p1.y, p2.y) <= point.y <= max(p1.y, p2.y):
                    return True
            elif p1.y == p2.y == point.y:  # Horizontal edge
                if min(p1.x, p2.x) <= point.x <= max(p1.x, p2.x):
                    return True

            if point.y > min(p1.y, p2.y):
                if point.y <= max(p1.y, p2.y):
                    if point.x <= max(p1.x, p2.x):
                        if p1.y != p2.y:
                            x_inters = (point.y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                        if p1.x == p2.x or point.x <= x_inters:
                            inside = not inside

            p1 = p2

        return inside

    @classmethod
    def rectangle(cls: type[T], corner1: Point2D, corner2: Point2D) -> T:
        upper_left = Point2D(min(corner1.x, corner2.x), min(corner1.y, corner2.y))
        upper_right = Point2D(max(corner1.x, corner2.x), min(corner1.y, corner2.y))
        lower_left = Point2D(min(corner1.x, corner2.x), max(corner1.y, corner2.y))
        lower_right = Point2D(max(corner1.x, corner2.x), max(corner1.y, corner2.y))
        return cls(tuple((upper_left, upper_right, lower_right, lower_left)))


@dataclass(frozen=True, unsafe_hash=True)
class Point2D:
    x: int
    y: int

    def __lt__(self, other: Self) -> Self:
        return self.x < other.x or (self.x == other.x and self.y < other.y)

    def manhattan_distance(self, other: Self) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def rectangle_area(self, other: Self) -> int:
        return (abs(self.x - other.x) + 1) * (abs(self.y - other.y) + 1)

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
    return next(iter(heapq.nlargest(
        1,
        (
            p1.rectangle_area(p2)
            for p1, p2 in combinations(points, 2)
        )
    )))


"""
--- Part Two ---
The Elves just remembered: they can only switch out tiles that are red or green. So, your rectangle can only include red or green tiles.

In your list, every red tile is connected to the red tile before and after it by a straight line of green tiles. The list wraps, so the first red tile is also connected to the last red tile. Tiles that are adjacent in your list will always be on either the same row or the same column.

Using the same example as before, the tiles marked X would be green:

..............
.......#XXX#..
.......X...X..
..#XXXX#...X..
..X........X..
..#XXXXXX#.X..
.........X.X..
.........#X#..
..............
In addition, all of the tiles inside this loop of red and green tiles are also green. So, in this example, these are the green tiles:

..............
.......#XXX#..
.......XXXXX..
..#XXXX#XXXX..
..XXXXXXXXXX..
..#XXXXXX#XX..
.........XXX..
.........#X#..
..............
The remaining tiles are never red nor green.

The rectangle you choose still must have red tiles in opposite corners, but any other tiles it includes must now be red or green. This significantly limits your options.

For example, you could make a rectangle out of red and green tiles with an area of 15 between 7,3 and 11,1:

..............
.......OOOOO..
.......OOOOO..
..#XXXXOOOOO..
..XXXXXXXXXX..
..#XXXXXX#XX..
.........XXX..
.........#X#..
..............
Or, you could make a thin rectangle with an area of 3 between 9,7 and 9,5:

..............
.......#XXX#..
.......XXXXX..
..#XXXX#XXXX..
..XXXXXXXXXX..
..#XXXXXXOXX..
.........OXX..
.........OX#..
..............
The largest rectangle you can make in this example using only red and green tiles has area 24. One way to do this is between 9,5 and 2,3:

..............
.......#XXX#..
.......XXXXX..
..OOOOOOOOXX..
..OOOOOOOOXX..
..OOOOOOOOXX..
.........XXX..
.........#X#..
..............
Using two red tiles as opposite corners, what is the largest area of any rectangle you can make using only red and green tiles?
"""


@example("""\
7,1
11,1
11,7
9,7
9,5
2,5
2,3
7,3
""", result=24)
@challenge(day=9)
def red_green(lines: list[str]) -> int:
    polygon = RectilinearPolygon(tuple(
        Point2D(*(int(n) for n in line.split(',')))
        for line in lines
        if line.strip()
    ))
    return next(iter(heapq.nlargest(
        1,
        (
            p1.rectangle_area(p2)
            for p1, p2 in combinations(polygon.points, 2)
            if RectilinearPolygon.rectangle(p1, p2) in polygon
        )
    )))
