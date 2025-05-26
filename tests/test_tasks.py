from __future__ import annotations

import pytest

from stelar.client import TaskSpec


@pytest.mark.skip()
def test_exec_word_count_manual(test_client):
    """
    Execute the word count task manually.
    """

    c = test_client
    d1 = c.datasets["shakespeare_novels"]

    # Create a process
    p1 = c.processes.get("word-count-tests")

    api_json = {
        "process_id": str(p1.id),
        # name: Optional, goes into tags
        "name": "Word Count on RJ",
        # Package name or id of the tool
        # If image is not provided, take the 'latest' (most recent) image of the tool
        # from the embedded repository
        # If image is provided use the image
        ### "tool": ""
        "image": "petroud/stelar-word-count:latest",
        #
        "inputs": {"text_to_count": ["d1::owned"]},
        "datasets": {
            "d1": str(d1.id),
            "d2": {
                "name": "the-results-of-word-count",
                "owner_org": "stelar-klms",
                "notes": "The result of map reduce word count",
                "tags": ["wordcount", "map-reduce"],
            },
        },
        # Use anything, not used
        "parameters": {"key": "value", "key1": 1},
        "outputs": {
            "word_count_file": {
                "url": "s3://test-bucket/word-count.txt",
                "dataset": "d2",
                "resource": {"name": "RJ Word Count 2", "relation": "owned"},
            }
        },
        "secrets": {"hello": "world"},
    }

    # Define the input and output files
    resp = c.POST("v2/task", **api_json)

    assert resp.status_code in range(
        200, 300
    ), f"Error: {resp.status_code} - {resp.text}"
    assert (
        resp.json()["status"] == "success"
    ), f"Error: {resp.status_code} - {resp.text}"


def test_task_spec(testcli):
    d1 = testcli.datasets["dataset1"]

    t = TaskSpec(name="Word Count on RJ")
    t.d("d1", d1)
    t.d(
        "d2",
        name="the-results-of-word-count",
        owner_org="stelar-klms",
        notes="The result of map reduce word count",
        tags=["wordcount", "map-reduce"],
    )
    t.i(text_to_count="d1::owned", profile=["d1::profile"])
    t.o(
        word_count_file={
            "url": "s3://test-bucket/word-count.txt",
            "dataset": "d2",
            "resource": {"name": "RJ Word Count 2", "relation": "owned"},
        }
    )
    t.p(key="value", key1=1)

    spec = t.spec()
    target = {
        "name": "Word Count on RJ",
        "datasets": {
            "d1": str(d1.id),
            "d2": {
                "name": "the-results-of-word-count",
                "owner_org": "stelar-klms",
                "notes": "The result of map reduce word count",
                "tags": ["wordcount", "map-reduce"],
            },
        },
        "inputs": {"text_to_count": ["d1::owned"], "profile": ["d1::profile"]},
        "outputs": {
            "word_count_file": {
                "url": "s3://test-bucket/word-count.txt",
                "dataset": "d2",
                "resource": {"name": "RJ Word Count 2", "relation": "owned"},
            }
        },
        "parameters": {
            "key": "value",
            "key1": 1,
        },
    }

    assert set(spec.keys()) == set(target.keys())
    for key in spec:
        assert spec[key] == target[key]


def test_task_spec_empty():
    t = TaskSpec()
    spec = t.spec()
    target = {
        "name": "task",
        "datasets": {},
        "inputs": {},
        "outputs": {},
        "parameters": {},
    }

    assert set(spec.keys()) == set(target.keys())
    for key in spec:
        assert spec[key] == target[key]


def test_task_spec_init(testcli):
    """
    Test the initialization of TaskSpec.
    """

    assert TaskSpec().tool is None
    assert TaskSpec().name == "task"
    assert TaskSpec().image is None

    assert TaskSpec("test-tool").tool == "test-tool"

    tool = testcli.tools["simple_tool"]
    assert TaskSpec(tool).tool == "simple_tool"
    assert TaskSpec(tool.id).tool == str(tool.id)
    assert TaskSpec(tool.name).tool == tool.name

    assert TaskSpec(tool).image is None
    assert TaskSpec(tool, image="latest").image == "latest"
    assert (
        TaskSpec(image="petroud/stelar-word-count:latest").image
        == "petroud/stelar-word-count:latest"
    )
    assert TaskSpec(image="petroud/stelar-word-count:latest").tool is None


def test_task_spec_dataset(testcli):
    """
    Test the dataset method of TaskSpec.
    """

    d1 = testcli.datasets["dataset1"]
    t = TaskSpec().d("d1", d1)
    assert t.datasets == {"d1": str(d1.id)}

    t = TaskSpec().d("d2", name="test-dataset", owner_org="stelar-klms")
    assert t.datasets == {"d2": {"name": "test-dataset", "owner_org": "stelar-klms"}}

    with pytest.raises(ValueError):
        t = TaskSpec().d("d3", d1, name="test-dataset", owner_org="stelar-klms")

    deforg = testcli.datasets.default_organization
    assert TaskSpec().d("d", name="foo", owner_org=deforg).datasets["d"][
        "owner_org"
    ] == str(deforg.id)

    assert TaskSpec().d("d", name="foo", owner_org=deforg.id).datasets["d"][
        "owner_org"
    ] == str(deforg.id)


def test_task_spec_input(testcli):
    """
    Test the input method of TaskSpec.
    """

    d = testcli.datasets["shakespeare_novels"]
    r = d.resources[0]
    rid = str(r.id)

    assert TaskSpec().i(inp=r).spec()["inputs"]["inp"] == [rid]
    assert TaskSpec().i(inp=rid).spec()["inputs"]["inp"] == [rid]

    assert TaskSpec().i(inp=[r]).spec()["inputs"]["inp"] == [rid]
    assert TaskSpec().i(inp=[rid]).spec()["inputs"]["inp"] == [rid]

    assert TaskSpec().i(inp=[r, r]).spec()["inputs"]["inp"] == [rid, rid]
    assert TaskSpec().i(inp=[rid, rid]).spec()["inputs"]["inp"] == [rid, rid]
    assert TaskSpec().i(inp=[r, rid]).spec()["inputs"]["inp"] == [rid, rid]
    assert TaskSpec().i(inp=[rid, r]).spec()["inputs"]["inp"] == [rid, rid]


def test_task_spec_output(testcli):
    """
    Test the output method of TaskSpec.
    """

    d = testcli.datasets["shakespeare_novels"]
    r = d.resources[0]
    rid = str(r.id)

    outspec = {"url": r.url}
    assert TaskSpec().o(out=outspec).spec()["outputs"]["out"] == {
        "url": r.url,
    }

    outspec = {"url": r.url, "resource": r}
    assert TaskSpec().o(out=outspec).spec()["outputs"]["out"] == {
        "url": r.url,
        "resource": str(r.id),
    }

    outspec = {
        "url": r.url,
        "dataset": str(d.id),
        "resource": {"name": r.name, "relation": "owned"},
    }
    assert TaskSpec().o(out=outspec).spec()["outputs"]["out"] == {
        "url": r.url,
        "dataset": str(d.id),
        "resource": {"name": r.name, "relation": "owned"},
    }


#
# TODO: Add more tests for task execution
#
def test_create_task(testcli):
    """
    Test the creation of a task.
    """

    d = testcli.datasets["shakespeare_novels"]
    proc = testcli.processes["word-count-tests"]
