import pytest

@pytest.mark.skip
def test_dataset_by_name(testcli):
    ds = testcli.get_dataset('new-package')
