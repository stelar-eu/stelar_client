from .base import BaseAPI
from .package import PackageCursor
from .tasks import TaskCursor
from .workflows import ProcessCursor, ToolCursor, Workflow


class WorkflowsAPI(BaseAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processes = ProcessCursor(self)
        self.tasks = TaskCursor(self)
        self.workflows = PackageCursor(self, Workflow)
        self.tools = ToolCursor(self)

        self.load_local_task_sigs()

    def load_local_task_sigs(self):
        """Load local task signatures from the local filesystem."""
        import csv
        from pathlib import Path

        lts_filepath = Path.home() / ".stelar_lts.csv"
        if lts_filepath.exists():
            with open(lts_filepath, newline="") as f:
                lts_reader = csv.reader(f, delimiter=",")
                self.local_task_sigs = {row[0]: row[1] for row in lts_reader}
        else:
            self.local_task_sigs = {}

    def commit_local_task_sig(self, task_id: str, sig: str):
        """Commit a local task signature to the local filesystem."""
        import csv
        from pathlib import Path

        lts_filepath = Path.home() / ".stelar_lts.csv"
        with open(lts_filepath, "a", newline="") as f:
            lts_writer = csv.writer(f, delimiter=",")
            lts_writer.writerow([task_id, sig])
        self.local_task_sigs[task_id] = sig
