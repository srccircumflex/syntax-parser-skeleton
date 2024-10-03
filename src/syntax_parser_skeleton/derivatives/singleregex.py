from re import search, Pattern

from syntax_parser_skeleton import *


class SingleRegexBranch(Branch):

    def ends(self, row_content: str, row_n: int, row_cursor: int, abs_cursor: int) -> NodeToken:
        return NodeToken(0, 0, "", row_n, row_cursor, abs_cursor, self)


class SingleRegexPhrase(Phrase):
    pattern: Pattern[str]

    def __init__(
            self,
            pattern: Pattern[str],
            id: Any = ""
    ):
        super().__init__(id)
        self.pattern = pattern

    def starts(self, row_content: str, row_n: int, row_cursor: int, abs_cursor: int, active_branch: SingleRegexBranch) -> SingleRegexBranch | None:
        if m := search(self.pattern, row_content):
            b = SingleRegexBranch(m.start(), m.end(), m.group(), row_n, row_cursor, abs_cursor, active_branch, self)
            return b
