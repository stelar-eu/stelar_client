"""

Author: Petrou Dimitrios 
Organization: Athena Research Center
Project Name:  STELAR EU 
Project Info: https://stelar-project.eu/

"""
# from typing import Any

from urllib.parse import urlparse

from minio.datatypes import Object

S3ObjSpec = str | tuple[str, str] | Object


def is_s3url(url: str) -> bool:
    """Check if a given URL is an S3 URL.

    Args:
        url (str): The URL to check.
    Returns:
        bool: True if the URL is an S3 URL, False otherwise.
    """
    u = urlparse(url)
    return u.scheme == "s3"


def s3spec_to_pair(objspec: S3ObjSpec) -> tuple[str, str]:
    """Converts an S3 object specification to a pair of bucket and object name.

    Args:
        objspec (S3ObjSpec): A URL (string), tuple of two strings,
        or minio.datatypes.Object instance representing an S3 object.
    Returns:
        tuple[str, str]: A pair of strings, representing the bucket and object name.
    """
    if isinstance(objspec, str):
        u = urlparse(objspec)
        if u.scheme != "s3":
            raise ValueError(f"Invalid S3 object url: {objspec}")
        bucket = u.netloc
        obj = u.path.lstrip("/")
        return bucket, obj
    elif isinstance(objspec, tuple) and len(objspec) == 2:
        return objspec
    elif isinstance(objspec, Object):
        return objspec.bucket_name, objspec.object_name
    else:
        raise TypeError(f"Invalid type S3 object spec: {repr(objspec)}")


def s3spec_to_dict(objspec: S3ObjSpec) -> dict[str, str]:
    """Converts an S3 object specification to a dictionary with bucket and object keys.

    The main use case for this function is to call client.s3 methods quickly:

    .. code-block:: python

        client.s3.get_object(**s3spec_to_dict("s3://bucket/object"))

    Args:
        objspec (S3ObjSpec): A URL (string), tuple of two strings,
        or minio.datatypes.Object instance representing an S3 object.
    Returns:
        dict[str, str]: A dictionary with keys "bucket_name" and "object_name".
    """
    bucket, obj = s3spec_to_pair(objspec)
    return {"bucket_name": bucket, "object_name": obj}


def s3spec_to_url(objspec: S3ObjSpec) -> str:
    """Converts an S3 object specification to a URL string.

    Args:
        objspec (S3ObjSpec): A URL (string), tuple of two strings,
        or minio.datatypes.Object instance representing an S3 object.
    Returns:
        str: A URL string representing the S3 object.
    """
    bucket, obj = s3spec_to_pair(objspec)
    return f"s3://{bucket}/{obj}"
