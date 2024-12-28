import pytest

from stelar_client import Client, Dataset

# @pytest.mark.skip
def test_dataset_by_name(testcli):
    d = testcli.registry_for(Dataset).fetch_proxy('fbfa243a-91a0-4150-8ea7-53b695fb0c54')
    
    assert d.name == 'new-package'
    assert d.resources[0].dataset is d

