from __future__ import annotations

from collections.abc import Iterable
from functools import cached_property
from typing import Any, Generator, overload


class Token:
    xml_label = "T"

    content: str
    match_rel_start: int
    match_rel_end: int
    row_n: int
    row_viewpoint: int
    abs_viewpoint: int

    parent_branch: Branch

    @cached_property
    def abs_start(self) -> int:
        return self.abs_viewpoint + self.match_rel_start

    @cached_property
    def start_in_row(self) -> int:
        return self.row_viewpoint + self.match_rel_start

    @cached_property
    def abs_end(self) -> int:
        return self.abs_viewpoint + self.match_rel_end

    @cached_property
    def end_in_row(self) -> int:
        return self.row_viewpoint + self.match_rel_end

    @property
    def index_in_branch(self) -> int:
        return self.parent_branch.stack.index(self)

    @property
    def right_neighbor(self) -> Token | NodeToken | Branch:
        return self.parent_branch[self.index_in_branch + 1]

    @property
    def left_neighbor(self) -> Token | NodeToken | Branch:
        return self.parent_branch[self.index_in_branch - 1]

    def __init__(
            self,
            match_rel_start: int,
            match_rel_end: int,
            matched_content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
            parent_branch: Branch
    ):
        self.match_rel_start = match_rel_start
        self.match_rel_end = match_rel_end
        self.content = matched_content
        self.row_n = row_n
        self.row_viewpoint = row_viewpoint
        self.abs_viewpoint = abs_viewpoint
        self.parent_branch = parent_branch

    def __lt__(self, other: Token) -> bool:
        return self.match_rel_start < other.match_rel_start

    def __repr__(self):
        return f"<{self.xml_label} coord='{self.row_n}:{self.start_in_row}:{self.end_in_row}/{self.abs_start}:{self.abs_end}'>{self.content!r}</{self.xml_label}>"

    def call_branch_start(self):
        ...

    def call_branch_extend(self):
        ...

    def call_branch_end(self):
        ...


class NodeToken(Token):
    xml_label = "N"


class Branch(Token):
    xml_label = "B"

    parent_branch: Branch
    phrase: Phrase | None
    stack: list[NodeToken | Token | Branch | NodeToken]

    @property
    def start_node(self) -> NodeToken:
        return self.stack[0]

    @property
    def end_node(self) -> NodeToken:
        return self.stack[-1]

    def __init__(
            self,
            match_rel_start: int,
            match_rel_end: int,
            matched_content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
            parent_branch: Branch | None,
            phrase: Phrase,
    ):
        Token.__init__(self, match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, parent_branch)
        self.parent_branch = parent_branch
        self.stack = [self.make_node(match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint)]
        self.phrase = phrase

    def make_node(
            self,
            match_rel_start: int,
            match_rel_end: int,
            matched_content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
    ) -> NodeToken:
        return NodeToken(match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, self)

    def make_token(
            self,
            match_rel_start: int,
            match_rel_end: int,
            matched_content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
    ) -> Token:
        return Token(match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, self)

    def extend_branch(
            self,
            match_rel_start: int,
            match_rel_end: int,
            content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
    ) -> Token:
        self.stack.append(lf := self.make_token(
            match_rel_start,
            match_rel_end,
            content,
            row_n,
            row_viewpoint,
            abs_viewpoint,
        ))
        return lf

    def gen_linear(self) -> Generator[Token, Any, None]:
        for i in self.stack:
            if isinstance(i, Token):
                yield i
            else:
                yield from i.gen_linear()

    def ends(
            self,
            row_content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
    ) -> NodeToken | None:
        return NodeToken(0, 0, "", row_n, row_viewpoint, abs_viewpoint, self)

    def next_search_content(self, search_content: str):
        return search_content

    def __lt__(self, other: Branch) -> bool:
        return self.stack[0] < other.stack[0]

    def __repr__(self):
        return f"<{self.xml_label} phrase='{self.phrase.id}'>{str().join(repr(i) for i in self.stack)}</{self.xml_label}>"

    def __iter__(self):
        return self.stack.__iter__()

    def __getitem__(self, __i):
        return self.stack.__getitem__(__i)

    def __len__(self):
        return self.stack.__len__()


class Phrase:
    id: Any
    sub_phrases: set[Phrase]

    def __init__(self, id: Any = ''):
        self.id = id
        self.sub_phrases = set()

    @overload
    def add_phrases(self, node: Phrase | Iterable[Phrase], *nodes: Phrase | Iterable[Phrase], mutual: bool = False) -> Phrase:
        ...

    def add_phrases(self, *nodes: Phrase | Iterable[Phrase], mutual: bool = False) -> Phrase:
        if mutual:
            def _i():
                nonlocal node
                if isinstance(node, Phrase):
                    self.sub_phrases.add(node)
                    node.sub_phrases.add(self)
                else:
                    self.sub_phrases |= set(node)
                    for _node in node:
                        _node.sub_phrases.add(self)
        else:
            def _i():
                nonlocal node
                if isinstance(node, Phrase):
                    self.sub_phrases.add(node)
                else:
                    self.sub_phrases |= set(node)
                
        for node in nodes:
            _i()

        return self

    def add_self(self) -> Phrase:
        self.sub_phrases.add(self)
        return self

    def starts(
            self,
            row_content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
            active_branch: Branch
    ) -> Branch | None:
        return Branch(0, len(row_content), row_content, row_n, row_viewpoint, abs_viewpoint, active_branch, self)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id!r}>"

