from __future__ import annotations
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Iterator, Self


@dataclass(slots=True)
class Node:
    """A node in the Dancing Links toroidal doubly-linked list."""

    up: Self = field(default=None, repr=False)  # type: ignore[assignment]
    down: Self = field(default=None, repr=False)  # type: ignore[assignment]
    left: Self = field(default=None, repr=False)  # type: ignore[assignment]
    right: Self = field(default=None, repr=False)  # type: ignore[assignment]
    column: ColumnHeader = field(default=None, repr=False)  # type: ignore[assignment]
    row_id: int = -1

    def __post_init__(self) -> None:
        # Self-linking by default (circular list of one)
        if self.up is None:
            self.up = self
        if self.down is None:
            self.down = self
        if self.left is None:
            self.left = self
        if self.right is None:
            self.right = self


@dataclass(slots=True)
class ColumnHeader(Node):
    """Column header node with size tracking and optional name."""

    size: int = 0
    name: str = ""
    is_primary: bool = True  # Primary columns must be covered exactly once


class DancingLinks[T]:
    """
    Dancing Links matrix supporting Algorithm X for exact cover problems.

    Generic over T, the type used to identify rows (placements).
    """

    def __init__(self) -> None:
        self.header = ColumnHeader(name="root")
        self.columns: dict[str, ColumnHeader] = {}
        self.rows: dict[int, T] = {}
        self._row_counter: int = 0

    def add_column(self, name: str, *, primary: bool = True) -> ColumnHeader:
        """Add a new column to the matrix."""
        col = ColumnHeader(name=name, is_primary=primary)
        col.column = col

        # Insert at end of header row (before header due to circular list)
        col.right = self.header
        col.left = self.header.left
        self.header.left.right = col
        self.header.left = col

        self.columns[name] = col
        return col

    def add_row(self, column_names: Iterable[str], row_data: T) -> int:
        """
        Add a row covering the specified columns.
        Returns the row ID.
        """
        row_id = self._row_counter
        self._row_counter += 1
        self.rows[row_id] = row_data

        first_node: Node | None = None
        prev_node: Node | None = None

        for col_name in column_names:
            col = self.columns[col_name]
            node = Node(column=col, row_id=row_id)

            # Vertical linking: insert at bottom of column
            node.down = col
            node.up = col.up
            col.up.down = node
            col.up = node
            col.size += 1

            # Horizontal linking
            if first_node is None:
                first_node = node
                prev_node = node
            else:
                node.left = prev_node
                prev_node.right = node  # type: ignore[union-attr]
                prev_node = node

        # Close the horizontal circular list
        if first_node is not None and prev_node is not None:
            prev_node.right = first_node
            first_node.left = prev_node

        return row_id

    def _cover(self, col: ColumnHeader) -> None:
        """Cover a column and all rows containing it."""
        col.right.left = col.left
        col.left.right = col.right

        node = col.down
        while node is not col:
            row_node = node.right
            while row_node is not node:
                row_node.down.up = row_node.up
                row_node.up.down = row_node.down
                row_node.column.size -= 1
                row_node = row_node.right
            node = node.down

    def _uncover(self, col: ColumnHeader) -> None:
        """Uncover a column (reverse of cover)."""
        node = col.up
        while node is not col:
            row_node = node.left
            while row_node is not node:
                row_node.column.size += 1
                row_node.down.up = row_node
                row_node.up.down = row_node
                row_node = row_node.left
            node = node.up

        col.right.left = col
        col.left.right = col

    def _choose_column(self) -> ColumnHeader | None:
        """Choose column with minimum size (MRV heuristic). Returns None if no primary columns remain."""
        min_size = float("inf")
        best_col: ColumnHeader | None = None

        col = self.header.right
        while col is not self.header:
            if isinstance(col, ColumnHeader) and col.is_primary:
                if col.size < min_size:
                    min_size = col.size
                    best_col = col
                    if min_size == 0:  # Can't do better than 0
                        break
            col = col.right

        return best_col

    def solve(self, *, find_all: bool = False) -> Iterator[list[T]]:
        """
        Solve the exact cover problem using Algorithm X.

        Yields solutions as lists of row data.
        If find_all is False, stops after first solution.
        """
        solution_stack: list[int] = []

        def search() -> Iterator[list[T]]:
            col = self._choose_column()

            # No primary columns left means we found a solution
            if col is None:
                yield [self.rows[row_id] for row_id in solution_stack]
                return

            # Empty column means dead end
            if col.size == 0:
                return

            self._cover(col)

            row_node = col.down
            while row_node is not col:
                solution_stack.append(row_node.row_id)

                # Cover all other columns in this row
                node = row_node.right
                while node is not row_node:
                    self._cover(node.column)
                    node = node.right

                yield from search()

                if not find_all and solution_stack:
                    # Check if we already yielded (hacky but works)
                    pass

                solution_stack.pop()

                # Uncover in reverse order
                node = row_node.left
                while node is not row_node:
                    self._uncover(node.column)
                    node = node.left

                row_node = row_node.down

            self._uncover(col)

        yield from search()

    def has_solution(self) -> bool:
        """Check if at least one solution exists."""
        return next(self.solve(), None) is not None
