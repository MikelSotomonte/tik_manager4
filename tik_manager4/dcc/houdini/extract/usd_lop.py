"""Extract USD from Houdini scene. lop version"""

import logging

import hou

from tik_manager4.dcc.extract_core import ExtractCore
from tik_manager4.dcc.houdini import utils

LOG = logging.getLogger(__name__)


class Usd(ExtractCore):
    """Extract USD from Houdini scene using the tik_rop node."""

    nice_name = "Usd_lop"
    optional = False
    color = (71, 143, 203)

    def __init__(self):
        
        # these are the exposed settings in the UI
        exposed_settings = {}
        super().__init__(exposed_settings=exposed_settings)
        if hou.isApprentice():
            self._extension = ".usdnc"
            self._message = "USD export is not supported in Houdini Apprentice. Format will be saved as .usdnc"
        else:
            self._extension = ".usd"
        # Category names must match to the ones in category_definitions.json (case sensitive)
        self.category_functions = {}

    def _extract_default(self):
        rop_lop = hou.node("/stage").node("tik_rop")
        """Extract method for any non-specified category"""
        # Single frame export
        _file_path = self.resolve_output()
        rop_lop.parm("lopoutput").set(_file_path)

        # set properties
        #rop_lop.parm("trange").set("off")

        rop_lop.parm("execute").pressButton()
        return True
