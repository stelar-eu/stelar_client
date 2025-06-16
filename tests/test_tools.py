import pytest
import requests

from stelar.client import *
from stelar.client.tool import ToolProfile


def create_test_tool(testcli: Client) -> Tool:
    tool = testcli.tools.create(
        name="test-tool",
        description="A tool for testing purposes",
        parameters={
            "x": "The x coordinate",
            "y": "The y coordinate",
            "z": "The z coordinate",
        },
        inputs={
            "map_file": "The file containing the map data",
            "vec_file": "The file containing the vector data",
        },
        outputs={
            "result": "The result of the tool execution",
            "log": "The log file of the tool execution",
        },
        profiles={
            "default": {
                "image": "v0.8",
                "memory_limit": "2G",
            },
            "large": {
                "image": "v0.8",
                "memory_limit": "4G",
            },
        },
    )
    return tool


@pytest.fixture
def test_tool(testcli):
    tool = create_test_tool(testcli)

    yield tool

    tool.delete()


def test_tool_creation(testcli, test_tool: Tool):
    tool = test_tool
    assert isinstance(tool, Tool), "The created object is not a Tool instance"

    try:
        assert tool.name == "test-tool"
        assert tool.description == "A tool for testing purposes"
        assert tool.parameters == {
            "x": "The x coordinate",
            "y": "The y coordinate",
            "z": "The z coordinate",
        }
        assert tool.inputs == {
            "map_file": "The file containing the map data",
            "vec_file": "The file containing the vector data",
        }
        assert tool.outputs == {
            "result": "The result of the tool execution",
            "log": "The log file of the tool execution",
        }
        assert tool.profiles == {
            "default": {
                "image": "v0.8",
                "memory_limit": "2G",
            },
            "large": {
                "image": "v0.8",
                "memory_limit": "4G",
            },
        }
    finally:
        tool.delete()


def test_tool_in_list(testcli, test_tool: Tool):
    assert "test-tool" in testcli.tools
    assert test_tool is testcli.tools["test-tool"]


def test_tool_category(test_tool):
    assert test_tool.category is None

    test_tool.category = "other"

    assert test_tool.category == "other"

    with pytest.raises(ValueError):
        test_tool.category = "invalid category"


def test_tool_repository(test_tool):
    assert test_tool.repository == test_tool.name


def test_tool_registry_access(testcli, test_tool: Tool):
    url = testcli.klms_info.klms_root_url.replace("klms.", "registry.")
    headers = {"Authorization": f"Bearer {testcli._token}"}
    response = requests.get(
        f"{url}/api/v1/repository/stelar/{test_tool.name}", headers=headers
    )
    assert (
        response.status_code == 200
    ), f"Failed to access the tool registry: {response.text}"
    repo = response.json()

    assert (
        repo["name"] == test_tool.name
    ), "The repository name does not match the tool name"


def test_tool_no_profiles(testcli):
    tool = testcli.tools.create(
        name="test-tool-no-profiles",
        description="A tool without profiles",
        parameters={},
        inputs={},
        outputs={},
    )

    try:
        assert tool.profiles == {}

        assert tool.get_profile() is None
        assert tool.get_profile("default") is None

        with pytest.raises(ValueError):
            tool.profiles = None

        tool.set_profile("default")
        assert tool.profiles["default"] == {}

        tool.set_profile("default", image="v0.8", memory_limit="2G")
        assert tool.profiles["default"] == {
            "image": "v0.8",
            "memory_limit": "2G",
        }

        tool.update_profile("default", image="v0.9")
        assert tool.profiles["default"] == {
            "image": "v0.9",
            "memory_limit": "2G",
        }

        tool.set_profile("default", memory_limit="3G")
        assert tool.profiles["default"] == {
            "memory_limit": "3G",
        }

        tool.delete_profile("default")
        assert "default" not in tool.profiles

    finally:
        tool.delete()


def test_tool_with_profiles(testcli, test_tool):
    tool = test_tool

    assert tool.profiles
    assert tool.get_profile("default") == ToolProfile(image="v0.8", memory_limit="2G")
    assert tool.get_profile("large") == ToolProfile(image="v0.8", memory_limit="4G")

    assert len(tool.profiles) == 2
    tool.delete_profile("default")


def test_tool_get_image(testcli):
    t = testcli.tools["simple_tool"]

    assert t.get_image().name == "0.2.0"
    assert t.get_image("0.2.0").name == "0.2.0"

    assert t.get_image("1.2.0") is None
    assert t.get_image("1.2.0", "v0.8") == "v0.8"
