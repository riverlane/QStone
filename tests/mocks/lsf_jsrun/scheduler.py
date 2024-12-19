"""Mock scheduler of lsf-jsrun."""

import re


class Scheduler:
    """Mocking class for lsf jsrun scheduler."""

    def run(self, src: str) -> bool:
        """Mock run and validator for bsub script.

        Parses the script checking for re matches of commands.

        Arguments:
            src: bsub source script to mock execute.

        Returns bsub script is valid.
        """

        assert src.startswith("#!/bin/bash")

        # BSUB option assertions

        assert re.search(r"#BSUB -P \S+", src)
        assert re.search(r"#BSUB -W \d.*", src)
        assert re.search(r"#BSUB -nnodes \d+", src)
        assert re.search(r"#BSUB -J \S+", src)
        assert re.search(r"#BSUB -o \S+", src)
        assert re.search(r"#BSUB -e \S+", src)

        # JSRUN job run assertions
        assert re.search("jsrun", src)

        return True
