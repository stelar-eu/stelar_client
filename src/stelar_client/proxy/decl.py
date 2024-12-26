from enum import Enum

class ProxyState(Enum):
    ERROR=0      # means that a proxy is no longer valid (maybe the entity was deleted?)
    EMPTY=1      # means that a proxy contains no entity data
    CLEAN=2      # means that a proxy contains entity data but no changes since last sync
    DIRTY=3      # means that a proxy contains changes since last sync
