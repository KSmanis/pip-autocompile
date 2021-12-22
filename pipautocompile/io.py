from re import compile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from re import RegexFlag
    from typing import Union

    from _typeshed import StrOrBytesPath


def file_contains_pattern(
    file: "Union[StrOrBytesPath, int]",
    pattern: str,
    *,
    flags: "Union[int, RegexFlag]" = 0,
) -> bool:
    try:
        f = open(file)
    except OSError:
        pass
    else:
        compiled_pattern = compile(pattern, flags)
        with f:
            for line in f:
                if compiled_pattern.search(line) is not None:
                    return True
    return False
