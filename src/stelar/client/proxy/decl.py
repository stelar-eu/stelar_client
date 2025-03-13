from __future__ import annotations

import re
from enum import Enum


class ProxyState(Enum):
    ERROR = 0  # means that a proxy is no longer valid (maybe the entity was deleted?)
    EMPTY = 1  # means that a proxy contains no entity data
    CLEAN = 2  # means that a proxy contains entity data but no changes since last sync
    DIRTY = 3  # means that a proxy contains changes since last sync


# -------------------------
# Tag-related declarations
# -------------------------
TAGNAME_PATTERN = re.compile(r"[A-Za-z0-9 _-]{2,100}")
TAGSPEC_PATTERN = re.compile(r"((.{2,100})\:)?([A-Za-z0-9 _-]{2,100})")


def validate_tagname(tagname: str) -> bool:
    """Check if a string is formatted correctly as a tagname"""
    return TAGNAME_PATTERN.fullmatch(tagname) is not None


def validate_tagspec(tagspec: str) -> bool:
    """Check if a string is formatted correctly as a tagspec"""
    return TAGSPEC_PATTERN.fullmatch(tagspec) is not None


def tag_split(tagspec: str) -> tuple[str | None, str]:
    """Split a tagspec into a pair or (<vocabulary-name> , <tag-name>).

    Properly, a tagspec is either <tag-name>  or <vocabulary-name>:<tag-name>,
    where

    <tagname>
        is a string made only of lower-case alphanumerics, hyphen (-) and underscore (_),
        and of length in [2,100]
    <vocabulary-name>
        is any string (which may contain spaces and other ascii characters) of
        length [2,100].

    Arguments
    ---------
        tagspec (str): the tag specification
    Returns
    -------
        (str|None, str): a pair of (<vocabulary-name> , <tag-name>)
    Raises
    ------
        ValueError: if the tagspec is not valid
    """
    m = TAGSPEC_PATTERN.fullmatch(tagspec)
    if m is None:
        raise ValueError("Invalid tag specification")
    return m.groups()[1:]


def tag_join(vocname: str | None, tagname: str) -> str:
    """Return the tagspec of a tag and a vocabulary.

    Args:
        vocname  (str|None): the vocabulary name
        tagname: the tag name
    Returns:
        (str) the tagspec
    """
    return f"{vocname}:{tagname}" if vocname is not None else tagname
