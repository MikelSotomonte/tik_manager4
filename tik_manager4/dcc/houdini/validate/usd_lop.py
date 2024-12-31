import hou
from tik_manager4.dcc.validate_core import ValidateCore

class ropChecker(ValidateCore):
    """Check for the tik_rop node, should be used with \"usd_lop\""""

    nice_name = "Check for \"tik_rop\""

    def __init__(self):
        super().__init__()
        self.autofixable = False
        self.ignorable = False
        self.selectable = False


    def collect(self):
        self.tikRop_node = hou.node("/stage").node("tik_rop")

    def validate(self):
        """Check if the hierarchy is correct."""
        self.collect()
        
        if not self.tikRop_node:
            self.failed(msg="No usd_rop called \"tik_rop\" found.")
            return
        
        if self.tikRop_node.type().name() != "usd_rop":
            self.failed(msg="The node called \"tik_rop\" is not a usd_rop.")
            return

        self.passed()