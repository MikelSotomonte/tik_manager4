# pylint: disable=super-with-arguments
# pylint: disable=consider-using-f-string
"""Publisher Handler module.

This module is responsible for handling the publish process.
"""

from pathlib import Path

from tik_manager4.core import filelog

from tik_manager4.dcc.standalone import main as standalone
from tik_manager4.objects.publish import PublishVersion
from tik_manager4.objects.guard import Guard

LOG = filelog.Filelog(logname=__name__, filename="tik_manager4")


class Publisher:
    """Publisher class to handle the publish process."""

    guard = Guard()

    def __init__(self, project_object):
        """Initialize the Publisher object."""
        self._dcc_handler = self.guard.dcc_handler
        self._project_object = project_object
        self._work_object = None
        self._work_version = None
        self._task_object = None
        self._metadata = None

        # resolved variables
        self._resolved_extractors = {}
        self._resolved_validators = {}
        self._abs_publish_data_folder = None
        self._abs_publish_scene_folder = None
        self._publish_file_name = None
        self._publish_version = None

        # classs variables

        self._published_object = None

    @property
    def validators(self):
        """List of resolved validators."""
        return self._resolved_validators

    @property
    def extractors(self):
        """List of resolved extractors."""
        return self._resolved_extractors

    @property
    def work_object(self):
        """The Work object that will be published."""
        return self._work_object

    def resolve(self):
        """Resolve the publish data file name.

        Returns:
            str: The resolved publish data file name.
        """
        self._work_object, self._work_version = self._project_object.get_current_work()

        if not self._work_object:
            LOG.warning("No work object found. Aborting.")
            return False

        self._resolved_extractors = {}
        self._resolved_validators = {}

        # get the task object
        self._task_object = self._project_object.find_task_by_id(
            self._work_object.task_id
        )
        # self._metadata = self._task_object.parent_sub.metadata
        self._metadata = self._task_object.metadata

        _category_definitons = self._work_object.guard.category_definitions
        extracts = _category_definitons.properties.get(
            self._work_object.category, {}
        ).get("extracts", [])
        validations = _category_definitons.properties.get(
            self._work_object.category, {}
        ).get("validations", [])
        # collect the matching extracts and validations from the dcc_handler.
        # dcc_extracts = [x.lower() for x in list(self._dcc_handler.extracts.keys())]
        category_extracts = [x.lower() for x in extracts]
        for extract in list(self._dcc_handler.extracts.keys()):
            if extract.lower() in category_extracts:
                self._resolved_extractors[extract] = self._dcc_handler.extracts[
                    extract
                ]()
                # define the category
                self._resolved_extractors[extract].category = self._work_object.category
                self._resolved_extractors[extract].metadata = self._metadata
            else:
                LOG.warning(
                    "Extract {0} defined in category settings but it is not available on {1}".format(
                        extract, self._dcc_handler.name
                    )
                )

        for validation in validations:
            if validation in list(self._dcc_handler.validations.keys()):
                self._resolved_validators[validation] = self._dcc_handler.validations[
                    validation
                ]()
                self._resolved_validators[validation].metadata = self._metadata
            else:
                LOG.warning(
                    "Validation {0} defined in category settings but it is not available on {1}".format(
                        validation, self._dcc_handler.name
                    )
                )

        latest_publish_version = self._work_object.publish.get_last_version()

        self._abs_publish_data_folder = (
            self._work_object.publish.get_publish_data_folder()
        )
        self._abs_publish_scene_folder = (
            self._work_object.publish.get_publish_project_folder()
        )
        self._publish_version = latest_publish_version + 1
        self._publish_file_name = (
            f"{self._work_object.name}_v{self._publish_version:03d}.tpub"
        )
        return self._publish_file_name

    def reserve(self):
        """Reserve the slot for publish.

        Makes sure that no other process overrides the publish.
        """
        # make sure the publish file is not already exists
        _publish_file_path = (
            Path(self._abs_publish_data_folder) / self._publish_file_name
        )
        if _publish_file_path.exists():
            raise ValueError(f"Publish file already exists. {_publish_file_path}")

        self._published_object = PublishVersion(str(_publish_file_path))

        self._published_object.add_property("name", self._work_object.name)
        self._published_object.add_property("creator", self._work_object.guard.user)
        self._published_object.add_property("category", self._work_object.category)
        self._published_object.add_property("dcc", self._work_object.guard.dcc)
        self._published_object.add_property(
            "publish_id", self._published_object.generate_id()
        )
        self._published_object.add_property("version_number", self._publish_version)
        self._published_object.add_property("work_version", self._work_version)
        self._published_object.add_property("task_name", self._work_object.task_name)
        self._published_object.add_property("task_id", self._work_object.task_id)
        self._published_object.add_property(
            "path", Path(self._work_object.path, "publish").as_posix()
        )
        self._published_object.add_property(
            "dcc_version", self._dcc_handler.get_dcc_version()
        )
        self._published_object.add_property("elements", [])

        self._published_object.apply_settings()  # make sure the file is created
        self._published_object.init_properties()  # make sure the properties are initialized
        self._published_object._dcc_handler.pre_publish()

    def validate(self):
        """Validate the scene using the resolved validators."""
        for _val_name, val_object in self._resolved_validators.items():
            val_object.validate()

    def write_protect(self, file_or_folder_path):
        """Protect the given file or folder making it read-only.

        Args:
            file_or_folder_path (str): The path to the file or folder.
        """
        path = Path(file_or_folder_path)
        file_list = []
        if path.is_file():
            file_list.append(path)
        elif path.is_dir():
            for _file in path.rglob("*"):
                file_list.append(_file)
        for _file in file_list:
            try:
                _file.chmod(0o444)
            except Exception as e:  # pylint: disable=broad-except
                LOG.warning(f"File protection failed: {_file}")

    def extract_single(self, extract_object):
        """Extract only from the given extract object.

        Args:
            extract_object (Extract): The extract object to extract.
        """
        publish_path = Path(
            self._work_object.get_abs_project_path("publish", self._work_object.name)
        )
        extract_object.category = self._work_object.category  # define the category
        extract_object.extract_folder = str(publish_path)  # define the extract folder
        extract_object.extract_name = f"{self._work_object.name}_v{self._publish_version:03d}"  # define the extract name
        extract_object.extract()
        self.write_protect(extract_object.resolve_output())

    def extract(self):
        """Extract the elements.

        Uses all resolved extractors to extract the elements.
        """
        # first save the scene
        self._dcc_handler.save_scene()
        publish_path = Path(
            self._work_object.get_abs_project_path("publish", self._work_object.name)
        )
        for _extract_type_name, extract_object in self._resolved_extractors.items():
            self.extract_single(extract_object)

    def publish(self, notes=None):
        """Finalize the publish by updating the reserved slot.

        Args:
            notes (str, optional): The notes to add to the publish.

        Returns:
            PublishVersion: The published object.
        """
        # collect the validation states and log it into the publish object
        validations = {}
        for validation_name, validation_object in self._resolved_validators.items():
            validations[validation_name] = validation_object.state
        self._published_object.add_property("validations", validations)

        # collect the extracted elements information and add to the publish object
        for _extract_type_name, extract_object in self._resolved_extractors.items():
            if (
                extract_object.state == "failed"
                or extract_object.state == "unavailable"
                or not extract_object.enabled
            ):
                continue
            element = {
                "name": extract_object.nice_name,
                "type": extract_object.name,
                "suffix": extract_object.extension,
                "path": Path(extract_object.resolve_output())
                .relative_to(self._published_object.get_abs_project_path())
                .as_posix(),
                "bundled": extract_object.bundled,
                "bundle_info": extract_object.bundle_info,
                "bundle_match_id": extract_object.bundle_match_id,
            }
            self._published_object._elements.append(element)

        self._published_object.edit_property(
            "elements", self._published_object._elements
        )
        if not notes:
            notes = "[Auto Generated]"
        self._published_object.add_property("notes", notes)

        self._generate_thumbnail()

        self._published_object.apply_settings(force=True)
        self._published_object._dcc_handler.post_publish()
        return self._published_object

    def _generate_thumbnail(self):
        """Generate the thumbnail."""
        thumbnail_name = f"{self._work_object.name}_v{self._publish_version:03d}.png"
        thumbnail_path = self._published_object.get_abs_database_path(
            "thumbnails", thumbnail_name
        )
        Path(thumbnail_path).parent.mkdir(parents=True, exist_ok=True)
        self._dcc_handler.generate_thumbnail(thumbnail_path, 220, 124)
        self._published_object.add_property(
            "thumbnail", Path("thumbnails", thumbnail_name).as_posix()
        )

    def discard(self):
        """Discard the reserved slot."""
        # find any extracted files and delete them
        for _extract_type_name, extract_object in self._resolved_extractors.items():
            if extract_object.state == "failed":
                continue
            _extracted_file_path = Path(extract_object.resolve_output())
            if _extracted_file_path.exists():
                # remove the write protection
                _extracted_file_path.chmod(0o777)
                _extracted_file_path.unlink()

        # delete the publish file
        _publish_file_path = (
            Path(self._abs_publish_data_folder) / self._publish_file_name
        )
        if _publish_file_path.exists():
            _publish_file_path.unlink()
        self._published_object = None
        LOG.info("Publish discarded.")

    @property
    def metadata(self):
        """Metadata associated with the parent subproject."""
        return self._metadata

    @property
    def publish_version(self):
        """Resolved publish version."""
        return self._publish_version

    @property
    def publish_name(self):
        """Resolved publish name."""
        return self._publish_file_name

    @property
    def absolute_data_path(self):
        """Resolved absolute data path."""
        return self._abs_publish_data_folder

    @property
    def absolute_scene_path(self):
        """Resolved absolute scene path."""
        return self._abs_publish_scene_folder

    @property
    def relative_data_path(self):
        """Resolved relative path."""
        if self._work_object:
            return (
                Path(self._abs_publish_data_folder)
                .relative_to(self._work_object.guard.project_root)
                .as_posix()
            )
        return None

    @property
    def relative_scene_path(self):
        """Resolved relative path."""
        if self._work_object:
            return (
                Path(self._abs_publish_scene_folder)
                .relative_to(self._work_object.guard.project_root)
                .as_posix()
            )
        return None


class SnapshotPublisher(Publisher):
    """Separate publisher to handle arbitrary file and folder publishing.

    Handles automatically creating a new work version if the current work is
    not there.
    """

    def __init__(self, *args):
        """Initialize the SnapshotPublisher object."""
        super(SnapshotPublisher, self).__init__(args)
        # this overrides the dcc handler which resolved on inherited
        # class to standalone
        self.__dcc_handler = standalone.Dcc()

    @property
    def work_object(self):
        """Work object."""
        return self._work_object

    @work_object.setter
    def work_object(self, value):
        """Set the work object.

        Args:
            value (Work): The work object.
        """
        self._work_object = value

    @property
    def work_version(self):
        """Work version."""
        return self._work_version

    @work_version.setter
    def work_version(self, value):
        """Set the work version.

        Args:
            value (int): The work version.
        """
        self._work_version = value

    def resolve(self):
        """Resolve the file name for the snapshot.

        Returns:
            str: The resolved publish file name.
        """

        version_dictionary = self._work_object.get_version(self._work_version)
        relative_path = version_dictionary.get("scene_path")
        abs_path = self._work_object.get_abs_project_path(relative_path)

        # get either the snapshot or snapshot_bundle depending if its a folder or file
        if Path(abs_path).is_dir():
            snapshot_extractor = self._dcc_handler.extracts["snapshot_bundle"]()
        else:
            snapshot_extractor = self._dcc_handler.extracts["snapshot"]()
        snapshot_extractor.category = self._work_object.category  # define the category

        snapshot_extractor.source_path = abs_path
        snapshot_extractor.extension = Path(abs_path).suffix

        self._resolved_extractors = {"snapshot": snapshot_extractor}
        self._resolved_validators = {}

        latest_publish_version = self._work_object.publish.get_last_version()

        self._abs_publish_data_folder = (
            self._work_object.publish.get_publish_data_folder()
        )
        self._abs_publish_scene_folder = (
            self._work_object.publish.get_publish_project_folder()
        )
        self._publish_version = latest_publish_version + 1
        self._publish_file_name = (
            f"{self._work_object.name}_v{self._publish_version:03d}.tpub"
        )
        return self._publish_file_name

    def _generate_thumbnail(self):
        """Generate the thumbnail."""
        thumbnail_name = f"{self._work_object.name}_v{self._publish_version:03d}.png"
        thumbnail_path = self._published_object.get_abs_database_path(
            "thumbnails", thumbnail_name
        )
        Path(thumbnail_path).parent.mkdir(parents=True, exist_ok=True)
        extension = self._resolved_extractors["snapshot"].extension or "Bundle"
        self._dcc_handler.text_to_image(
            extension, thumbnail_path, 220, 124, color="cyan"
        )
        self._published_object.add_property(
            "thumbnail", Path("thumbnails", thumbnail_name).as_posix()
        )
