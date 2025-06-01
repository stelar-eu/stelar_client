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
        "name": "unnamed",
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
    assert TaskSpec().name is None
    assert TaskSpec().image is None

    assert TaskSpec("test-tool").tool == "test-tool"

    tool = testcli.tools["simple_tool"]
    assert TaskSpec(tool).tool == str(tool.id)
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

    # Add raw url
    ts.i(raw_url="s3://klms-bucket/iris.csv")

    # Add url from process context
    ts.i(ctx_file="ctx::testing")

    t = proc.run(ts)
    assert t.exec_state == "created"
    tin = t.job_input

    assert tin["input"]["iris"] == [str(iris.resources[0].url)]
    assert tin["input"]["wine"] == [str(wine.resources[0].url)]
    assert tin["input"]["shakespeare"] == [str(shakespeare.resources[0].url)]
    assert tin["input"]["wine_alias"] == [str(wine.resources[0].url)]
    assert tin["input"]["raw_url"] == ["s3://klms-bucket/iris.csv"]
    assert tin["input"]["ctx_file"] == ["s3://klms-bucket/wordcount.csv"]

    t.exit_job()
    t.delete()


def test_create_task_with_outputs(testcli):
    """
    Test the creation of a task with outputs.
    """

    c = testcli
    proc = c.processes["simple_proc"]
    stelar_klms = c.organizations["stelar-klms"]

    if "test_dataset" in c.datasets:
        c.datasets["test_dataset"].delete(purge=True)
    if "output_dataset" in c.datasets:
        c.datasets["output_dataset"].delete(purge=True)

    test_dataset = c.datasets.create(
        name="test_dataset", organization=stelar_klms, title="Test Dataset"
    )
    test_dataset.add_resource(
        name="Test resource0", url="s3://klms-bucket/badfile0.csv"
    )
    test_dataset.add_resource(
        name="Test resource1", url="s3://klms-bucket/badfile1.csv"
    )
    test_dataset.add_resource(
        name="Test resource2", url="s3://klms-bucket/badfile2.csv"
    )

    ts = TaskSpec()
    ts.d("output_dataset", name="output_dataset", owner_org="stelar-klms")
    ts.d("test_dataset", test_dataset)

    ts.o(
        outfile1={
            "url": "s3://klms-bucket/output1.csv",
            "dataset": "output_dataset",
            "resource": {
                "name": "Output Resource",
                "relation": "owned",
            },
        },
        outfile2={
            "url": "s3://klms-bucket/output2.csv",
            "dataset": "ctx",
            "resource": {
                "name": "Output Resource 2",
                "relation": "temporary",
            },
        },
        outfile3={
            "url": "s3://klms-bucket/output3.csv",
            "resource": test_dataset.resources[0],
        },
        outfile4={
            "url": "s3://klms-bucket/output4.csv",
            "resource": test_dataset.resources[1].id,
        },
        outfile5={
            "url": "s3://klms-bucket/output5.csv",
            "resource": str(test_dataset.resources[2].id),
        },
        outfile6={
            "url": "s3://klms-bucket/output6.csv",
        },
    )

    proc_numres = len(proc.resources)
    t = proc.run(ts)
    assert t.exec_state == "created"
    targs = t.job_input

    assert targs["output"]["outfile1"] == "s3://klms-bucket/output1.csv"
    assert targs["output"]["outfile2"] == "s3://klms-bucket/output2.csv"
    assert targs["output"]["outfile3"] == "s3://klms-bucket/output3.csv"
    assert targs["output"]["outfile4"] == "s3://klms-bucket/output4.csv"
    assert targs["output"]["outfile5"] == "s3://klms-bucket/output5.csv"
    assert targs["output"]["outfile6"] == "s3://klms-bucket/output6.csv"

    # Create the data files
    fs = c.s3fs()
    for oname, ourl in targs["output"].items():
        fs.pipe_file(ourl, "This is the test file for " + oname)

    t.exit_job(message="Test task completed successfully", output=targs["output"])

    assert t.exec_state == "succeeded"

    # Check the resource for output1
    assert "output_dataset" in c.datasets
    output_dataset = c.datasets["output_dataset"]
    assert len(output_dataset.resources) == 1
    assert output_dataset.resources[0].url == "s3://klms-bucket/output1.csv"
    assert output_dataset.resources[0].name == "Output Resource"
    assert output_dataset.resources[0].relation == "owned"

    # Check the resource for output2
    assert len(proc.resources) == (proc_numres + 1)
    assert proc.resources[1].url == "s3://klms-bucket/output2.csv"
    assert proc.resources[1].name == "Output Resource 2"
    assert proc.resources[1].relation == "temporary"

    # Check the resource for output3
    assert len(test_dataset.resources) == 3
    assert test_dataset.resources[0].url == "s3://klms-bucket/output3.csv"
    assert test_dataset.resources[0].name == "Test resource0"

    # Check the resource for output4
    assert test_dataset.resources[1].url == targs["output"]["outfile4"]
    assert test_dataset.resources[1].name == "Test resource1"

    # Check the resource for output5
    assert test_dataset.resources[2].url == targs["output"]["outfile5"]
    assert test_dataset.resources[2].name == "Test resource2"

    # Delete catalog entries
    t.delete()
    proc.resources[1].delete()
    output_dataset.delete(purge=True)
    test_dataset.delete(purge=True)

    # Delete the output files
    for ourl in targs["output"].values():
        fs.rm(ourl)


def test_create_task_with_metrics(testcli):
    """
    Test the creation of a task with metrics.
    """

    c = testcli
    proc = c.processes["simple_proc"]

    ts = TaskSpec()
    t = proc.run(ts)
    assert t.exec_state == "created"

    mymetrics = dict(
        metric_obj={
            "value": 42,
            "description": "The answer to life, the universe, and everything",
        },
        metric_vec=[3.14, 2.71, 1.41],
        metric_str="a string",
        metric_num=12345,
        metric_null=None,
        metric_bool=True,
    )

    t.exit_job(
        message="Test task with metrics completed successfully", metrics=mymetrics
    )

    for metric in mymetrics:
        t.metrics[metric] == mymetrics[metric]
    t.delete()


def test_create_task_with_secrets(testcli):
    """
    Test the creation of a task with secrets.
    """

    c = testcli
    proc = c.processes["simple_proc"]

    ts = TaskSpec()
    secrets = {"secret_key": "secret_value"}
    t = proc.run(ts, secrets=secrets)
    assert t.exec_state == "created"

    targs = t.job_input
    assert targs["secrets"] == secrets

    t.fail("Test task with secrets failed")
    t.delete()
