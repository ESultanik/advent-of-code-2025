from collections.abc import Collection, Set
from typing import Generic, Hashable, TypeVar

T = TypeVar("T", bound="Hashable")


class Subset(Generic[T], Set[T]):
    def __init__(self, disjoint_set: DisjointSet[T], item: T) -> None:
        self.disjoint_set: DisjointSet[T] = disjoint_set
        self.item: T = item

    def union(self, other: Subset[T]) -> Subset[T]:
        if self.disjoint_set is not other.disjoint_set:
            raise ValueError("Can only union subsets belonging to the same disjoint set")
        elif other.item == self.item:
            return self
        a, b = self.item, other.item
        if self.disjoint_set.ranks[a] < self.disjoint_set.ranks[b]:
            a, b = b, a
        self.disjoint_set.parents[b] = a
        if self.disjoint_set.ranks[a] == self.disjoint_set.ranks[b]:
            self.disjoint_set.ranks[a] += 1
        assert any(i is p for i, p in self.disjoint_set.parents.items())
        return Subset(self.disjoint_set, a)

    def add(self, item: T) -> Subset[T]:
        if item not in self.disjoint_set:
            self.disjoint_set.add(item)
        return self.union(self.disjoint_set[item])

    def __iter__(self) -> Iterator[T]:
        for item in self.disjoint_set.parents.keys():
            if item in self:
                yield item

    def __len__(self) -> int:
        return sum(1 for item in self.disjoint_set.parents.keys() if self.disjoint_set[item] == self)

    def __contains__(self, item: T) -> bool:
        return self.disjoint_set[item] == self

    def __hash__(self) -> int:
        return hash(self.item)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Subset) and self.disjoint_set == other.disjoint_set and self.item == other.item

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.item!r})"


class DisjointSet(Generic[T], Collection[Subset[T]]):
    def __init__(self):
        self.parents: dict[T, T] = {}
        self.ranks: dict[T, int] = {}

    def __len__(self) -> int:
        return sum(1 for item, parent in self.parents.items() if item is parent)

    def __contains__(self, item: T) -> bool:
        return item in self.parents

    def __iter__(self) -> Iterator[Subset[T]]:
        for item, parent in self.parents.items():
            if item is parent:
                yield Subset(self, item)

    def add(self, item: T) -> Subset[T]:
        if item not in self:
            self.parents[item] = item
            self.ranks[item] = 0
        return self.find(item)

    def find(self, item: T) -> Subset[T]:
        if item not in self:
            raise KeyError(f"Item {item!r} not in disjoint set")
        path: list[T] = []
        while self.parents[item] is not item:
            path.append(item)
            item = self.parents[item]
        # path compression:
        for p in path:
            self.parents[p] = item
        return Subset(self, item)

    def union(self, item1: T, item2: T) -> Subset[T]:
        return self.add(item1).union(self.add(item2))

    __getitem__ = find
