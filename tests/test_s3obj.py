import pytest
from minio.datatypes import Object

from stelar.client.mutils import s3spec_to_pair


def test_s3objspec_to_pair():
    assert s3spec_to_pair("s3://bucket/object") == ("bucket", "object")
    assert s3spec_to_pair("s3:///object") == ("", "object")
    assert s3spec_to_pair("s3:///") == ("", "")
    assert s3spec_to_pair(("bucket", "object")) == ("bucket", "object")
    assert s3spec_to_pair(Object("bucket", "object")) == ("bucket", "object")
    assert s3spec_to_pair("s3://bucket/") == ("bucket", "")
    assert s3spec_to_pair("s3://bucket/a/bct") == ("bucket", "a/bct")
    assert s3spec_to_pair("s3://bucket") == ("bucket", "")
    assert s3spec_to_pair(("bucket", "")) == ("bucket", "")
    assert s3spec_to_pair(("bucket", "object")) == ("bucket", "object")


def test_s3objspec_to_pair_invalid():
    with pytest.raises(ValueError):
        s3spec_to_pair("http://bucket/object")
    with pytest.raises(TypeError):
        s3spec_to_pair(123)
    with pytest.raises(TypeError):
        s3spec_to_pair(("bucket", "object", "extra"))
    with pytest.raises(ValueError):
        s3spec_to_pair("//bucket/object")
    with pytest.raises(ValueError):
        s3spec_to_pair("/bucket/object")
    with pytest.raises(ValueError):
        s3spec_to_pair("bucket/object")
    with pytest.raises(ValueError):
        s3spec_to_pair("/object")
    with pytest.raises(ValueError):
        s3spec_to_pair("object")
    with pytest.raises(ValueError):
        s3spec_to_pair("")


def test_open_text_file(testcli):
    path = "s3://klms-bucket/rj.txt"

    with testcli.s3fs_open(path, mode="rb") as f:
        data = f.read()
        assert type(data) == bytes

    with testcli.s3.get_object(bucket_name="klms-bucket", object_name="rj.txt") as o:
        assert o.data == data

    with testcli.s3fs_open(path, mode="r") as f:
        data = f.read()
        assert type(data) == str


def test_create_text_file(testcli):
    path = "s3://klms-bucket/hello.txt"
    data = "Hello, World!"

    with testcli.s3fs_open(path, mode="w") as f:
        print("Hello, World!", file=f)

    with testcli.s3fs_open(path, mode="r") as f:
        assert f.read() == data + "\n"
