from uuid import UUID

import pytest

from stelar.client.proxy.exceptions import EntityNotFound


@pytest.fixture(autouse=True)
def tlicense(testcli):
    """Test fetching a license."""
    lic = testcli.licenses.create(
        title="Test License",
        key="test-license",
        description="A license for testing purposes.",
        url="https://example.com/test-license",
        osi_approved=True,
        open_data_approved=False,
    )

    yield lic.key

    try:
        lic.delete(purge=True)
    except Exception:
        pass


def test_create_license(testcli):
    try:
        lic = testcli.licenses.create(
            title="Test License",
            key="test-license2",
            description="A license for testing purposes.",
            url="https://example.com/test-license",
            osi_approved=True,
            open_data_approved=False,
        )
        """Test creating a license."""
        license = testcli.licenses.get("test-license")
        assert license is not None
        assert license.title == "Test License"
    finally:
        lic.delete()


def test_update_license(testcli):
    """Test updating a license."""
    license = testcli.licenses.get("test-license")
    assert license is not None

    license.title = "Updated Test License"
    license.description = "An updated description for testing purposes."

    updated_license = testcli.licenses.get("test-license")
    assert updated_license.title == "Updated Test License"
    assert updated_license.description == "An updated description for testing purposes."


def test_delete_license(testcli):
    """Test deleting a license."""
    license = testcli.licenses.get("test-license")
    assert license is not None
    license.delete()
    assert "test-license" not in testcli.licenses


def test_list_licenses(testcli):
    """Test listing all licenses."""
    assert "mit" in testcli.licenses
    assert "test-license" in testcli.licenses


def test_license_properties(testcli):
    """Test license properties."""
    license = testcli.licenses.get("test-license")
    assert license is not None

    assert isinstance(license.id, UUID)
    assert isinstance(license.key, str)
    assert isinstance(license.title, str)
    assert isinstance(license.description, str)
    assert isinstance(license.url, str)
    assert isinstance(license.osi_approved, bool)
    assert isinstance(license.open_data_approved, bool)


def test_license_proxy(testcli):
    """Test the LicensedProxy functionality."""
    license = testcli.licenses.get("test-license")
    assert license is not None


def test_dataset_license(testcli):
    """Test setting a license on a dataset."""

    d = testcli.datasets["dataset1"]

    # Clear the license
    d.license_id = None
    assert d.license_id is None
    assert d.license is None

    # Set the license to a string via license_id
    d.license_id = "test-license"
    assert d.license_id == "test-license"
    assert d.license.key == "test-license"

    # set the license via license
    d.license = "mit"
    assert d.license_id == "mit"
    assert d.license.key == "mit"

    # set via object
    d.license = testcli.licenses["test-license"]
    assert d.license_id == "test-license"
    assert d.license.key == "test-license"

    # set via UUID
    mitid = str(testcli.licenses["mit"].id)

    d.license = mitid
    assert d.license_id == mitid
    assert d.license.key == "mit"


def test_dataset_license_unknown(testcli):
    """Test setting a license to None on a dataset."""
    d = testcli.datasets["dataset1"]

    # Clear the license
    old_license = d.license
    with pytest.raises(EntityNotFound):
        d.license_id = "custom"
    assert d.license is old_license
