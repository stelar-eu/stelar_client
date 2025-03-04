from minio.datatypes import Object

from stelar.client.mutils import s3spec_to_pair


def test_s3objspec_to_pair():
    assert s3spec_to_pair("s3://bucket/object") == ("bucket", "object")
    assert s3spec_to_pair(("bucket", "object")) == ("bucket", "object")
    assert s3spec_to_pair(Object("bucket", "object")) == ("bucket", "object")

    assert s3spec_to_pair("s3://bucket/") == ("bucket", "")
    assert s3spec_to_pair("s3://bucket/a/bct") == ("bucket", "a/bct")
    assert s3spec_to_pair("s3://bucket") == ("bucket", "")
