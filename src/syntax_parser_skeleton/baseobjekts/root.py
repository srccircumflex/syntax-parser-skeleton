from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from baseobjekts.components import Phrase, Branch, Token, NodeToken


class RootToken(Token):
    xml_label = "RT"


class RootNodeToken(NodeToken):
    xml_label = "RN"


class RootBranch(Branch):
    xml_label = "RB"

    parent_branch: None

    def ends(self, row_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int) -> None:
        return None

    def __lt__(self, other: Branch) -> bool:
        pass

    def make_node(self, match_rel_start: int, match_rel_end: int, matched_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int) -> NodeToken:
        return RootNodeToken(match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, self)

    def make_token(self, match_rel_start: int, match_rel_end: int, matched_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int) -> Token:
        return RootToken(match_rel_start, match_rel_end, matched_content, row_n, row_viewpoint, abs_viewpoint, self)

    def __init__(self, root: Root):
        Branch.__init__(self, 0, 0, "", 0, 0, 0, None, Phrase())
        self.phrase = root


class _ParseFin(Exception):
    ...


class Root(Phrase):

    @dataclass
    class _Crawler:
        remain_row_content: str
        main_content: list[str]
        row_n: int
        row_viewpoint: int
        abs_viewpoint: int
        active_branch: Branch

        def __call__(self):
            sub_starts = list()
            _remain_row_content = self.remain_row_content
            for sn in self.active_branch.phrase.sub_phrases:
                if start_node := sn.starts(self.remain_row_content, self.row_n, self.row_viewpoint, self.abs_viewpoint, self.active_branch):
                    sub_starts.append(start_node)
                    _remain_row_content = start_node.next_search_content(_remain_row_content)
            active_stop = self.active_branch.ends(_remain_row_content, self.row_n, self.row_viewpoint, self.abs_viewpoint)

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
                    self.active_branch.extend_branch(
                        0, active_stop.match_rel_start,
                        self.remain_row_content[:active_stop.match_rel_start],
                        self.row_n, self.row_viewpoint, self.abs_viewpoint
                    ).call_branch_extend()
                self.active_branch.stack.append(active_stop)
                self.active_branch = self.active_branch.parent_branch
                self.remain_row_content = self.remain_row_content[active_stop.match_rel_end:]
                self.abs_viewpoint += active_stop.match_rel_end
                if not self.remain_row_content:
                    _nextrow()
                else:
                    self.row_viewpoint += active_stop.match_rel_end
                active_stop.call_branch_end()

            if sub_starts:
                sub_start = min(sub_starts)
                if active_stop and active_stop < sub_start.start_node:
                    _active_stop()
                else:
                    if sub_start.start_node.match_rel_start:
                        self.active_branch.extend_branch(
                            0, sub_start.start_node.match_rel_start,
                            self.remain_row_content[:sub_start.start_node.match_rel_start],
                            self.row_n, self.row_viewpoint, self.abs_viewpoint
                        ).call_branch_extend()
                    self.active_branch.stack.append(sub_start)
                    self.active_branch = sub_start
                    self.remain_row_content = self.remain_row_content[sub_start.start_node.match_rel_end:]
                    self.abs_viewpoint += sub_start.start_node.match_rel_end
                    if not self.remain_row_content:
                        _nextrow()
                    else:
                        self.row_viewpoint += sub_start.start_node.match_rel_end
                    sub_start.start_node.call_branch_start()
            elif active_stop:
                _active_stop()
            else:
                self.active_branch.extend_branch(
                    0, len(self.remain_row_content),
                    self.remain_row_content,
                    self.row_n, self.row_viewpoint, self.abs_viewpoint
                ).call_branch_extend()
                self.abs_viewpoint += len(self.remain_row_content)
                _nextrow()

    def __init__(self, id: Any = ""):
        Phrase.__init__(self, id)

    def starts(self, row_content: str, row_n: int, row_viewpoint: int, abs_viewpoint: int, active_branch: Branch) -> None:
        return None

    def parse(self, content: list[str]) -> Branch:
        main_branch = RootBranch(self)
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
