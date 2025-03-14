"""Utilities related to the Pandas library."""
import pathlib
import re
from typing import TYPE_CHECKING, Optional, Type, TypeVar
from urllib.parse import urlparse
from uuid import UUID

import pandas as pd

if TYPE_CHECKING:
    from .client import Client
    from .proxy import Proxy, ProxyList, ProxyVec

    ProxyClass = TypeVar("ProxyClass", bound=Proxy)


PANDAS_FORMATS = [
    "csv",
    "excel",
    "feather",
    "json",
    "parquet",
    "pickle",
    "stata",
    "table",
    "xml",
]

# List of pairs (regex, format) to match file extensions to formats
FILEEXT_MATCH = [
    (r"\.csv$", "csv"),
    (r"\.xls$", "excel"),
    (r"\.xlsx$", "excel"),
    (r"\.feather$", "feather"),
    (r"\.json$", "json"),
    (r"\.parquet$", "parquet"),
    (r"\.pkl$", "pickle"),
    (r"\.dta$", "stata"),
    (r"\.tsv$", "table"),
    (r"\.xml$", "xml"),
]


def _infer_format(path: str, hint: str = None) -> Optional[str]:
    """Infer the format of a file from its extension, or a hint."""

    try:
        hint = hint.lower()
        if hint in PANDAS_FORMATS:
            return hint
    except Exception:
        pass

    try:
        path = urlparse(path).path
        ext = pathlib.PurePath(path).suffix
        for regex, fmt in FILEEXT_MATCH:
            if re.search(regex, ext):
                return fmt
        else:
            return None
    except Exception:
        return None


def read_dataframe(client: Client, path: str, format=None, **kwargs) -> pd.DataFrame:
    """Read a DataFrame from a file.

    This function reads a DataFrame from a file and returns it.

    Parameters
    ----------"
    client : Client
        The client to use to read the file.
    path : str
        The path to the file to read."
    format : str, optional
        The format of the file to read. If not specified, the format will be
        inferred from the file extension.
    kwargs : dict
        Additional keyword arguments to pass to the read"
    """

    fmt = _infer_format(path, format)
    if fmt is None:
        raise ValueError(f"Cannot infer format for file {path}")

    pdreader = getattr(pd, f"read_{fmt}")
    return pdreader(path, storage_options=client.s3_access_data(), **kwargs)


@pd.api.extensions.register_series_accessor("stelar")
class StelarSeriesAccessor:
    def __init__(self, ds: pd.Series):
        self.ds = ds

    def to_proxy_vec(self, client: Client, proxy_type: Type[ProxyClass]) -> ProxyList:
        """Convert a series of UUIDs to a proxy vector.

        All items in the series are expected to be UUIDs. In particular,
        None, NA and missing values are not allowed.
        """
        if not self.ds.map(lambda x: isinstance(x, UUID)).all():
            raise ValueError("The series must contain only UUIDs")
        return ProxyVec(client, proxy_type, self.ds.to_list())

    def getattr(self, name, default=pd.NA):
        """Retrieve an attribute from all objects in a series.

        This is particularly useful when the series contains proxy objects.
        """
        return self.ds.map(lambda x: getattr(x, name, default))


@pd.api.extensions.register_dataframe_accessor("stelar")
class StelarDataFrameAccessor:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def write_dataset(self, client: Client, path: str, format=None, **kwargs):
        """Write a DataFrame to a file.

        This function writes a DataFrame to a file.

        Parameters
        ----------
        client : Client
            The client to use to write the file.
        path : str
            The path to the file to write.
        format : str, optional
            The format of the file to write. If not specified, the format will be
            inferred from the file extension.
        kwargs : dict
            Additional keyword arguments to pass to the write
        """

        fmt = _infer_format(path, format)
        if fmt is None:
            raise ValueError(f"Cannot infer format for file {path}")

        pdwriter = getattr(self.df, f"to_{fmt}")
        return pdwriter(path, storage_options=client.s3_access_data(), **kwargs)
