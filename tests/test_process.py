from stelar.client import Client, Process, Workflow


# @pytest.fixture(autouse=True, scope="module")
def cleanup_processes(testcontext):
    c = Client(testcontext)

    # Run after the tests in the module
    yield None

    for p in c.processes[:]:
        try:
            if "test_delete" in p.tags:
                p.delete()
                assert p not in c.processes
                c.DC.dataset_purge(id=str(p.id))
        except Exception:
            pass


def test_process_create(testcli):
    p = Process.new(testcli)
    assert p.organization is testcli.organizations["stelar-klms"]
    assert p.exec_state == "running"
    assert p.state == "active"
    assert p.creator == "admin"

    assert p.tasks == []

    p.terminate("succeeded")
    assert p.exec_state == "succeeded"
    p.tags += ("test_delete",)
    p.delete()


def test_process_create_with_workflow(testcli):
    wf = Workflow.new(testcli, name="test_workflow")

    p = Process.new(testcli, workflow=wf)
    assert p.workflow is wf
    assert p.exec_state == "running"
    assert p.state == "active"
    assert p.creator == "admin"

    assert p.tasks == []

    assert p.workflow is wf

    # Check updates to workflow
    p.workflow = None
    assert p.workflow is None
    p.workflow = wf
    assert p.workflow is wf

    p.terminate("succeeded")
    assert p.exec_state == "succeeded"
    p.tags += ("test_delete",)
    p.delete()
    wf.delete(purge=True)
