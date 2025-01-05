"""Extract USD from Houdini scene. lop version"""

import logging

import hou

from tik_manager4.dcc.extract_core import ExtractCore
from tik_manager4.dcc.houdini import utils

LOG = logging.getLogger(__name__)


class Usd(ExtractCore):
    """Extract USD from Houdini scene using the tik_rop node."""

    nice_name = "Usd Lop"
    optional = False
    color = (71, 143, 203)

    def __init__(self):
        if hou.isApprentice():
            self._message = "USD export is not supported in Houdini Apprentice. Format will be saved as .usdnc"
            global_exposed_settings = {
                    "format": {
                        "type": "combo",
                        "value": ".usdnc",
                        "items": [".usdnc"]
                    },
                }
        else:
            global_exposed_settings = {
                    "format": {
                        "type": "combo",
                        "value": ".usd",
                        "items": [".usd", ".usda"]
                    },
                }
        # these are the exposed settings in the UI
        exposed_settings = {}
        super().__init__(exposed_settings=exposed_settings, global_exposed_settings=global_exposed_settings)
        
        
        # Category names must match to the ones in category_definitions.json (case sensitive)
        self.category_functions = {}

    def _extract_default(self):
        self._extension = self.global_settings.get("format")
        rop_lop = hou.node("/stage").node("tik_rop")
        """Extract method for any non-specified category"""
        # Single frame export
        _file_path = self.resolve_output()
        rop_lop.parm("lopoutput").set(_file_path)

        # set properties
        #rop_lop.parm("trange").set("off")

        rop_lop.parm("execute").pressButton()
        return True
