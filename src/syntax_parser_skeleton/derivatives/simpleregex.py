from re import search, Pattern

from syntax_parser_skeleton import *


class SimpleRegexBranch(Branch):

    stop_pattern: Pattern[str]

    def ends(self, row_content: str, row_n: int, row_cursor: int, abs_cursor: int) -> NodeToken:
        if m := search(self.stop_pattern, row_content):
            return NodeToken(m.start(), m.end(), m.group(), row_n, row_cursor, abs_cursor, self)


class SimpleRegexPhrase(Phrase):
    start_pattern: Pattern[str]
    stop_pattern: Pattern[str]

    def __init__(
            self,
            start_pattern: Pattern[str],
            stop_pattern: Pattern[str],
            id: Any = ""
    ):
        super().__init__(id)
        self.start_pattern = start_pattern
        self.stop_pattern = stop_pattern

    def starts(self, row_content: str, row_n: int, row_cursor: int, abs_cursor: int, active_branch: SimpleRegexBranch) -> SimpleRegexBranch | None:
        if m := search(self.start_pattern, row_content):
            b = SimpleRegexBranch(m.start(), m.end(), m.group(), row_n, row_cursor, abs_cursor, active_branch, self)
            b.stop_pattern = self.stop_pattern
            return b

