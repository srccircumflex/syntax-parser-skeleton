from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
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

    root: RootBranch
    branch: Branch

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
        return self.branch.stack.index(self)

    @property
    def right_neighbor(self) -> Token | NodeToken | Branch:
        return self.branch[self.index_in_branch + 1]

    @property
    def left_neighbor(self) -> Token | NodeToken | Branch:
        return self.branch[self.index_in_branch - 1]

    def __init__(
            self,
            match_rel_start: int,
            match_rel_end: int,
            matched_content: str,
            row_n: int,
            row_viewpoint: int,
            abs_viewpoint: int,
            branch: Branch
    ):
        self.match_rel_start = match_rel_start
        self.match_rel_end = match_rel_end
        self.content = matched_content
        self.row_n = row_n
        self.row_viewpoint = row_viewpoint
        self.abs_viewpoint = abs_viewpoint
        self.branch = branch
        self.root = branch.root

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
            branch: Branch,
            phrase: Phrase,
    ):
        Token.__init__(self, match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, branch)
        self.branch = branch
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
            if isinstance(i, Branch):
                yield from i.gen_linear()
            else:
                yield i

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
            branch: Branch
    ) -> Branch | None:
        return Branch(0, len(row_content), row_content, row_n, row_viewpoint, abs_viewpoint, branch, self)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id!r}>"


class RootToken(Token):
    xml_label = "RT"


class RootNodeToken(NodeToken):
    xml_label = "RN"


class RootBranch(Branch):
    xml_label = "RB"

    def ends(self, row_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int) -> None:
        return None

    def __lt__(self, other: Branch) -> bool:
        pass

    def make_node(self, match_rel_start: int, match_rel_end: int, matched_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int) -> NodeToken:
        return RootNodeToken(match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, self)

    def make_token(self, match_rel_start: int, match_rel_end: int, matched_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int) -> Token:
        return RootToken(match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, self)

    def __init__(self, root_phrase: RootPhrase):
        self.root = self
        Branch.__init__(self, 0, 0, "", 0, 0, 0, self, root_phrase)


class _ParseFin(Exception):
    ...


class RootPhrase(Phrase):

    @dataclass
    class _Crawler:
        remain_row_content: str
        main_content: list[str]
        row_n: int
        row_viewpoint: int
        abs_viewpoint: int
        branch: Branch

        def __call__(self):
            sub_starts = list()
            _remain_row_content = self.remain_row_content
            for sn in self.branch.phrase.sub_phrases:
                if start_node := sn.starts(self.remain_row_content, self.row_n, self.row_viewpoint, self.abs_viewpoint, self.branch):
                    sub_starts.append(start_node)
                    _remain_row_content = start_node.next_search_content(_remain_row_content)
            active_stop = self.branch.ends(_remain_row_content, self.row_n, self.row_viewpoint, self.abs_viewpoint)

            def _nextrow():
                try:
                    self.remain_row_content = self.main_content.pop(0)
                except IndexError:
                    raise _ParseFin
                else:
                    self.row_n += 1
                    self.row_viewpoint = 0

            def _active_stop():
                if active_stop.match_rel_start:
                    self.branch.extend_branch(
                        0, active_stop.match_rel_start,
                        self.remain_row_content[:active_stop.match_rel_start],
                        self.row_n, self.row_viewpoint, self.abs_viewpoint
                    ).call_branch_extend()
                self.branch.stack.append(active_stop)
                self.branch = self.branch.branch
                self.remain_row_content = self.remain_row_content[active_stop.match_rel_end:]
                self.abs_viewpoint += active_stop.match_rel_end
                active_stop.call_branch_end()
                if not self.remain_row_content:
                    _nextrow()
                else:
                    self.row_viewpoint += active_stop.match_rel_end

            if sub_starts:
                sub_start = min(sub_starts)
                if active_stop and active_stop < sub_start.start_node:
                    _active_stop()
                else:
                    if sub_start.start_node.match_rel_start:
                        self.branch.extend_branch(
                            0, sub_start.start_node.match_rel_start,
                            self.remain_row_content[:sub_start.start_node.match_rel_start],
                            self.row_n, self.row_viewpoint, self.abs_viewpoint
                        ).call_branch_extend()
                    self.branch.stack.append(sub_start)
                    self.branch = sub_start
                    self.remain_row_content = self.remain_row_content[sub_start.start_node.match_rel_end:]
                    self.abs_viewpoint += sub_start.start_node.match_rel_end
                    sub_start.start_node.call_branch_start()
                    if not self.remain_row_content:
                        _nextrow()
                    else:
                        self.row_viewpoint += sub_start.start_node.match_rel_end
            elif active_stop:
                _active_stop()
            else:
                self.branch.extend_branch(
                    0, len(self.remain_row_content),
                    self.remain_row_content,
                    self.row_n, self.row_viewpoint, self.abs_viewpoint
                ).call_branch_extend()
                self.abs_viewpoint += len(self.remain_row_content)
                _nextrow()

    def __init__(self, id: Any = ""):
        Phrase.__init__(self, id)

    def starts(self, row_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int, branch: Branch) -> None:
        return None

    def make_rootbranch(self) -> RootBranch:
        return RootBranch(self)

    def parse(self, content: list[str]) -> RootBranch:
        main_branch = self.make_rootbranch()
        try:
            row_content = content.pop(0)
        except IndexError:
            return main_branch
        else:
            crawler = self._Crawler(row_content, content, 0, 0, 0, main_branch)
            try:
                while True:
                    crawler()
            except _ParseFin:
                branch = main_branch
                while isinstance(branch[-1], Branch):
                    branch = branch[-1]
                end_node = branch[-1]
                main_branch.stack.append(
                    main_branch.make_node(
                        end_node.match_rel_end,
                        end_node.match_rel_end,
                        "",
                        end_node.row_n,
                        end_node.row_viewpoint,
                        end_node.abs_viewpoint,
                    )
                )
                return main_branch
