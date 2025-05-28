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

    proc = testcli.processes["simple_proc"]
    task = proc.run(TaskSpec())

    assert task.exec_state == "created"
    assert task.process is proc
    assert task.inputs == {}

    task.exit_job()
    assert task.exec_state == "succeeded"

    task.delete()


def test_create_task_with_fail(testcli):
    """
    Test the creation of a task that fails.
    """

    proc = testcli.processes["simple_proc"]
    task = proc.run(TaskSpec())

    assert task.exec_state == "created"
    assert task.process is proc
    assert task.inputs == {}
    assert task.parameters is None

    assert not hasattr(task, "outputs")
    assert not hasattr(task, "messages")

    # Simulate a failure
    task.fail("Simulated failure")

    assert task.exec_state == "failed"
    assert task.messages == "Simulated failure"

    task.delete()


def test_create_task_params(testcli):
    """
    Test the creation of a task with parameters.
    """

    proc = testcli.processes["simple_proc"]
    task = proc.run(
        TaskSpec().p(
            str_param="test",
            int_param=42,
            composite={"key": "value"},
            listparam=["item1", "item2"],
        )
    )
    assert task.exec_state == "created"
    assert task.process is proc
    assert task.inputs == {}
    assert task.parameters == {
        "str_param": "test",
        "int_param": 42,
        "composite": {"key": "value"},
        "listparam": ["item1", "item2"],
    }

    task.exit_job()
    task.delete()


def test_create_task_with_inputs(testcli):
    # Testing for different types of input declarations

    c = testcli
    proc = c.processes["simple_proc"]

    shakespeare = c.datasets["shakespeare_novels"]
    iris = c.datasets["iris"]
    wine = c.datasets["wine"]

    ts = TaskSpec()

    ts.d("wine_quality", wine)

    # Add from resource
    ts.i(iris=iris.resources[0])

    # Add from resource id
    ts.i(wine=str(wine.resources[0].id))

    # Add from dataset and relation
    ts.i(shakespeare=f"{shakespeare.id}::owned")

    # Add from dataset and relation with alias
    ts.i(wine_alias="wine_quality::owned")

    t = proc.run(ts)
    assert t.exec_state == "created"
    tin = t.job_input

    assert tin["input"]["iris"] == [str(iris.resources[0].url)]
    assert tin["input"]["wine"] == [str(wine.resources[0].url)]
    assert tin["input"]["shakespeare"] == [str(shakespeare.resources[0].url)]
    assert tin["input"]["wine_alias"] == [str(wine.resources[0].url)]

    t.exit_job()
    t.delete()
