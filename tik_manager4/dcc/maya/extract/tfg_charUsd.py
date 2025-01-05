"""Extract Alembic characters with layer picking from Maya scene"""

from maya import cmds
from maya import OpenMaya as om
from tik_manager4.dcc.extract_core import ExtractCore
from tik_manager4.dcc.maya import utils


# The Collector will only collect classes inherit ExtractCore
class Usd(ExtractCore):
    """Extract usd from Maya scene"""

    nice_name = "USD characters"
    color = (71, 143, 203)

    # these are the exposed settings in the UI
    # WARNING: Caution removing keys from this dict! It will likely throw a KeyError on the _extract_* methods

    def __init__(self):
        #        "testCheck: ": {
#                    "display_name": "Test Check",
#                    "type": "boolean",
#                    "value": True,
#                    },

        display_layers = cmds.ls(type="displayLayer")
        global layerPrefix
        layerPrefix = "charExport_"
        global layerDict
        layerDict = {}
        # Remove the default "defaultLayer"
        if "defaultLayer" in display_layers:
            display_layers.remove("defaultLayer")
        char_list = []
        for layer in display_layers:
            if layerPrefix in layer:
                id = str(len(layerDict))
                key = id + "_" + layer.split(layerPrefix,1)[1]
                layerDict[key] = layer
                char_list.append(key)
                
        #layerDict[layer.split(layerPrefix,1)[1]] = layer.split(layerPrefix,1)[0]
        #cmds.menuItem(label=layer.split(layerPrefix,1)[1]) 
        # selected_layer = layerDict[charName] + layerPrefix + charName
        _ranges = utils.get_ranges()
        global_exposed_settings = {
            "characters":{
                "type": "list",
                "value": char_list
            },
            "start_frame": {
                "display_name": "Start Frame",
                "type": "integer",
                "value": _ranges[0],
            },
            "end_frame": {
                "display_name": "End Frame",
                "type": "integer",
                "value": _ranges[3],
            },
            "euler_filter": {
                "display_name": "Euler Filter",
                "type": "boolean",
                "value": False,
            },
            "static_single_sample": {
                "display_name": "Static Single Sample",
                "type": "boolean",
                "value": False,
            },
        }

        super(Usd, self).__init__(global_exposed_settings=global_exposed_settings)
        if not cmds.pluginInfo("mayaUsdPlugin", loaded=True, query=True):
            try:
                cmds.loadPlugin("mayaUsdPlugin")
            except Exception as e:
                om.MGlobal.displayInfo("USD Plugin cannot be initialized")
                raise e

        om.MGlobal.displayInfo("USD Extractor loaded")

        self._extension = ".usd"

    def _extract_default(self):
        """Extract method for animation category"""
        _file_path = self.resolve_output()
        settings = self.global_settings
        _start_frame = settings.get("start_frame")
        _end_frame = settings.get("end_frame")
        cmds.select(clear=True)
        _characters = settings.get("characters")
        for char in _characters:
            selected_layer = layerDict[char]
            objects_in_layer = cmds.editDisplayLayerMembers(selected_layer, query=True) or []
            # Select the objects in the layer
            if objects_in_layer:
                cmds.select(objects_in_layer, add=True)
            # selected_objects = cmds.ls(selection=True)
        cmds.mayaUSDExport(
            file=_file_path,
            exportBlendShapes=False,
            exportSkels=None,
            exportSkin=None,
            exportMaterialCollections=False,
            eulerFilter=settings.get("euler_filter"),
            frameRange=[_start_frame, _end_frame],
            ignoreWarnings=True,
            renderableOnly=False,
            selection=True,
            #metersPerUnit=0.01, doesnt seem to work
            rootPrim = "char",
            exportMaterials = False,
            stripNamespaces = True,
        )