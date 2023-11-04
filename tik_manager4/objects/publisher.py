# pylint: disable=super-with-arguments
# pylint: disable=consider-using-f-string
"""Publisher Handler."""

import pathlib

from tik_manager4.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="tik_manager4")

from tik_manager4 import dcc
from tik_manager4.objects.publish import Publish

class Publisher():
    _dcc_handler = dcc.Dcc()

    def __init__(self, work_object):
        """Initialize the Publisher object."""
        self._work_object = work_object

        # resolved variables
        self._resolved_extracts = {}
        self._resolved_validations = {}
        self._abs_publish_data_folder = None
        self._publish_file_name = None

        # classs variables

        self._published_object = None

    def resolve(self):
        """Resolve the validations, extracts, variables, etc."""

        _category_definitons = self._work_object.guard.category_definitions
        extracts = _category_definitons.get(self._work_object.category, {}).get("extracts", [])
        validations = _category_definitons.get(self._work_object.category, {}).get("validations", [])
        # collect the matching extracts and validations from the dcc_handler.
        for extract in extracts:
            if extract in self._dcc_handler.extracts.keys():
                self._resolved_extracts[extract] = self._dcc_handler.extracts[extract]
            else:
                LOG.warning("Extract {0} defined in category settings but it is not available on {1}".format(extract, self._dcc_handler.name))
        for validation in validations:
            if validation in self._dcc_handler.validations.keys():
                self._resolved_validations[validation] = self._dcc_handler.validations[validation]
            else:
                LOG.warning("Validation {0} defined in category settings but it is not available on {1}".format(validation, self._dcc_handler.name))

        # resolve the publish data path
        self._abs_publish_data_folder = self._work_object.get_abs_database_path("publish")

        # get the highest version from the _work_objects publishes
        # TODO - this is not working
        # _publishes_versions = list(self._work_object.publishes.values())
        # latest_publish_version = max(_publishes_versions) if _publishes_versions else 0
        # self._publish_file_name = f"{self._work_object.name}_v{latest_publish_version+1:03d}.tpub"



    def reserve(self):
        """Reserve the slot for publish.

        Makes sure that the publish is not overriden by other users during the process.
        """
        # make sure the publish file is not already exists
        _publish_file_path = pathlib.Path(self._abs_publish_data_folder) / self._publish_file_name
        if _publish_file_path.exists():
            raise ValueError(f"Publish file already exists. {_publish_file_path}")

        # add the publish to the work object
        self._work_object


    def validate(self):
        """Validate the scene."""
        pass

    def extract(self):
        """Extract the elements."""
        for extract_name, extract_class in self._dcc_handler.extracts.items():
            extractor = extract_class() # initialize the extractor
            extractor.category = self._work_object.category # define the category


    def publish(self):
        """Finalize the publish by updating the reserved slot."""
        pass