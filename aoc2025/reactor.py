"""
--- Day 11: Reactor ---
You hear some loud beeping coming from a hatch in the floor of the factory, so you decide to check it out. Inside, you find several large electrical conduits and a ladder.

Climbing down the ladder, you discover the source of the beeping: a large, toroidal reactor which powers the factory above. Some Elves here are hurriedly running between the reactor and a nearby server rack, apparently trying to fix something.

One of the Elves notices you and rushes over. "It's a good thing you're here! We just installed a new server rack, but we aren't having any luck getting the reactor to communicate with it!" You glance around the room and see a tangle of cables and devices running from the server rack to the reactor. She rushes off, returning a moment later with a list of the devices and their outputs (your puzzle input).

For example:

aaa: you hhh
you: bbb ccc
bbb: ddd eee
ccc: ddd eee fff
ddd: ggg
eee: out
fff: out
ggg: out
hhh: ccc fff iii
iii: out
Each line gives the name of a device followed by a list of the devices to which its outputs are attached. So, bbb: ddd eee means that device bbb has two outputs, one leading to device ddd and the other leading to device eee.

The Elves are pretty sure that the issue isn't due to any specific device, but rather that the issue is triggered by data following some specific path through the devices. Data only ever flows from a device through its outputs; it can't flow backwards.

After dividing up the work, the Elves would like you to focus on the devices starting with the one next to you (an Elf hastily attaches a label which just says you) and ending with the main output to the reactor (which is the device with the label out).

To help the Elves figure out which path is causing the issue, they need you to find every path from you to out.

In this example, these are all of the paths from you to out:

Data could take the connection from you to bbb, then from bbb to ddd, then from ddd to ggg, then from ggg to out.
Data could take the connection to bbb, then to eee, then to out.
Data could go to ccc, then ddd, then ggg, then out.
Data could go to ccc, then eee, then out.
Data could go to ccc, then fff, then out.
In total, there are 5 different paths leading from you to out.

How many different paths lead from you to out?
"""

from collections import defaultdict, deque
from typing import Hashable, Iterable, TypeVar

from . import challenge, example

T = TypeVar("T", bound=Hashable)


def count_paths(edges: Iterable[tuple[T, T]], source: T, sink: T) -> int:
    """
    Count paths from source to sink.
    Raises ValueError if the graph contains a cycle.
    """
    edges = frozenset(edges)
    graph: dict[T, set[T]] = defaultdict(set)
    in_degree: dict[T, int] = defaultdict(int)
    for u, v in edges:
        graph[u].add(v)
        if v not in graph:
            graph[v] = set()
        in_degree[v] += 1

    # Kahn's algorithm for topological sort
    queue = deque([node for node in graph.keys() if in_degree[node] == 0])
    topo_order: list[T] = []

    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # cycle detection: if we couldn't process all nodes, there's a cycle
    if len(topo_order) != len(graph):
        raise ValueError("Graph contains a cycle!")

    # count paths with dynamic programming
    paths: dict[T, int] = defaultdict(int)
    paths[source] = 1

    for node in topo_order:
        for neighbor in graph[node]:
            paths[neighbor] += paths[node]

    return paths[sink]


def parse_edges(lines: list[str]) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for line in lines:
        colon_pos = line.index(":")
        assert colon_pos > 0
        from_node = line[:colon_pos].strip()
        for to_node in line[colon_pos + 1:].strip().split(" "):
            edges.append((from_node, to_node))
    return edges


@example("""\
aaa: you hhh
you: bbb ccc
bbb: ddd eee
ccc: ddd eee fff
ddd: ggg
eee: out
fff: out
ggg: out
hhh: ccc fff iii
iii: out
""", result=5)
@challenge(day=11)
def different_paths(lines: list[str]) -> int:
    return count_paths(parse_edges(lines), "you", "out")


def edges_without(edges: Iterable[tuple[T, T]], *nodes: T) -> list[tuple[T, T]]:
    nodes = frozenset(nodes)
    return [
        (from_node, to_node)
        for from_node, to_node in edges
        if from_node not in nodes and to_node not in nodes
    ]


@example("""\
svr: aaa bbb
aaa: fft
fft: ccc
bbb: tty
tty: ccc
ccc: ddd eee
ddd: hub
hub: fff
eee: dac
dac: fff
fff: ggg hhh
ggg: out
hhh: out
""", result=2)
@challenge(day=11)
def dac_fft(lines: list[str]) -> int:
    edges = parse_edges(lines)
    # first, calculate how many paths pass through neither dac nor fft
    paths_without_dac_fft = count_paths(edges_without(edges, "dac", "fft"), "svr", "out")
    # next, calculate how many paths pass through just dac
    paths_through_just_dac = count_paths(edges_without(edges, "fft"), "svr", "out") \
                             - paths_without_dac_fft
    # finally, calculate how many paths pass through just fft
    paths_through_just_fft = count_paths(edges_without(edges, "dac"), "svr", "out") \
                             - paths_without_dac_fft
    return count_paths(parse_edges(lines), "svr", "out") - paths_without_dac_fft \
           - paths_through_just_dac - paths_through_just_fft
