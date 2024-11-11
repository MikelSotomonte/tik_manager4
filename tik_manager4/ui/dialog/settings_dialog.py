# pylint: disable=import-error
"""Dialog for settings."""

import sys  # This is required for the 'frozen' attribute DO NOT REMOVE
from pathlib import Path
import logging

from tik_manager4.ui.Qt import QtWidgets, QtCore
from tik_manager4.ui.widgets import value_widgets
from tik_manager4.ui.widgets.validated_string import ValidatedString
from tik_manager4.ui.widgets.switch_tree import SwitchTreeWidget, SwitchTreeItem
from tik_manager4.ui.widgets.common import (
    HeaderLabel,
    ResolvedText,
    TikButtonBox,
    TikButton,
    TikIconButton,
    VerticalSeparator,
)
from tik_manager4.ui.dialog.feedback import Feedback
from tik_manager4.ui.dialog.user_dialog import NewUserDialog
from tik_manager4.ui.layouts.settings_layout import (
    SettingsLayout,
    convert_to_ui_definition,
    convert_to_settings_data,
    guess_data_type,
)
from tik_manager4.ui.dialog.data_containers import MainLayout
from tik_manager4 import management

LOG = logging.getLogger(__name__)


class SettingsDialog(QtWidgets.QDialog):
    """Settings dialog."""

    def __init__(self, main_object, *args, **kwargs):
        """Initiate the class."""
        super().__init__(*args, **kwargs)

        # DYNAMIC VARIABLES
        self._setting_widgets = []
        self.settings_list = []  # list of settings objects
        self.feedback = Feedback(parent=self)
        self.main_object = main_object
        self.layouts = MainLayout()
        self.setWindowTitle("Settings")
        self.menu_tree_widget: QtWidgets.QTreeWidget
        self.apply_button: QtWidgets.QPushButton
        self._validations_and_extracts = (
            None  # for caching the validations and extracts
        )
        self.error_count: int = 0
        # Execution
        self.build_ui()

        # expand everything
        self.menu_tree_widget.expandAll()

    def build_ui(self):
        """Build the UI."""
        self.build_layouts()
        self.build_static_widgets()
        self.create_content()
        # set the first item on menu tree as current
        self.menu_tree_widget.setCurrentItem(self.menu_tree_widget.topLevelItem(0))
        self.resize(960, 630)
        self.layouts.splitter.setSizes([250, 750])

    def build_layouts(self):
        """Build layouts."""
        self.layouts.master_layout = QtWidgets.QVBoxLayout(self)
        self.layouts.splitter = QtWidgets.QSplitter(self)

        left_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.left_layout = QtWidgets.QVBoxLayout(left_widget)
        self.layouts.left_layout.setContentsMargins(0, 0, 0, 0)

        right_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.right_layout = QtWidgets.QVBoxLayout(right_widget)
        self.layouts.right_layout.setContentsMargins(0, 0, 0, 0)
        self.layouts.master_layout.addWidget(self.layouts.splitter)
        self.layouts.buttons_layout = QtWidgets.QHBoxLayout()
        self.layouts.master_layout.addLayout(self.layouts.buttons_layout)

    def build_static_widgets(self):
        """Build static widgets."""

        self.menu_tree_widget = SwitchTreeWidget(user=self.main_object.user)
        self.menu_tree_widget.setRootIsDecorated(True)
        self.menu_tree_widget.setHeaderHidden(True)
        self.menu_tree_widget.header().setVisible(False)
        self.layouts.left_layout.addWidget(self.menu_tree_widget)

        tik_button_box = TikButtonBox(parent=self)
        self.layouts.buttons_layout.addWidget(tik_button_box)
        self.apply_button = tik_button_box.addButton(
            "Apply", QtWidgets.QDialogButtonBox.ApplyRole
        )
        self.apply_button.setEnabled(False)
        cancel_button = tik_button_box.addButton(
            "Cancel", QtWidgets.QDialogButtonBox.RejectRole
        )
        ok_button = tik_button_box.addButton(
            "Ok", QtWidgets.QDialogButtonBox.AcceptRole
        )

        # SIGNALS
        self.apply_button.clicked.connect(self.apply_settings)
        cancel_button.clicked.connect(self.close)
        ok_button.clicked.connect(lambda: self.apply_settings(close_dialog=True))

        self.layouts.buttons_layout.addWidget(tik_button_box)

    def create_content(self):
        """Create the content."""
        self.menu_tree_widget.clear()
        self.user_title()
        self.project_title()
        self.common_title()
        self.create_content_links()

    def user_title(self):
        """Create the user settings."""
        # create the menu items
        user_widget_item = SwitchTreeItem(["User"], permission_level=0)
        self.menu_tree_widget.addTopLevelItem(user_widget_item)

        # create sub-branches
        user_settings_item = SwitchTreeItem(["User Settings"], permission_level=0)
        user_widget_item.addChild(user_settings_item)
        ui_definition = {
            "commonFolder": {
                "display_name": "Common Folder",
                "tooltip": "The folder where the common data for all projects is stored.",
                "type": "pathBrowser",
                "value": self.main_object.user.settings.get_property("commonFolder"),
            },
            "user_templates_directory": {
                "display_name": "User Templates Directory",
                "tooltip": "The folder where all user template files stored for all Dccs. Supports flags.",
                "type": "pathBrowser",
                "value": self.main_object.user.settings.get_property(
                    "user_templates_directory"
                ),
            },
            "alembic_viewer": {
                "display_name": "Alembic Viewer",
                "tooltip": "The path to the Alembic Viewer executable. Supports flags.",
                "type": "fileBrowser",
                "value": self.main_object.user.settings.get_property("alembic_viewer"),
            },
            "usd_viewer": {
                "display_name": "USD Viewer",
                "tooltip": "The path to the USD Viewer executable. Supports flags.",
                "type": "fileBrowser",
                "value": self.main_object.user.settings.get_property("usd_viewer"),
            },
            "fbx_viewer": {
                "display_name": "FBX Viewer",
                "tooltip": "The path to the FBX Viewer executable. Supports flags.",
                "type": "fileBrowser",
                "value": self.main_object.user.settings.get_property("fbx_viewer"),
            },
            "image_viewer": {
                "display_name": "Image Viewer",
                "tooltip": "The path to the Image Viewer executable. Supports flags.",
                "type": "fileBrowser",
                "value": self.main_object.user.settings.get_property("image_viewer"),
            },
            "sequence_viewer": {
                "display_name": "Sequence Viewer",
                "tooltip": "The path to the Sequence Viewer executable. Supports flags.",
                "type": "fileBrowser",
                "value": self.main_object.user.settings.get_property("sequence_viewer"),
            },
            "video_player": {
                "display_name": "Video Viewer",
                "tooltip": "The path to the Video Player executable. Supports flags.",
                "type": "fileBrowser",
                "value": self.main_object.user.settings.get_property("video_player"),
            },
        }

        user_settings_item.content = self.__create_generic_settings_layout(
            settings_data=self.main_object.user.settings,
            title="User Settings",
            ui_definition=ui_definition,
        )

        user_password_item = SwitchTreeItem(["Change Password"], permission_level=0)
        user_widget_item.addChild(user_password_item)
        user_password_item.content = self.__create_user_password_layout()

    def __create_user_password_layout(self):
        """Create the widget for changing the user password."""
        content_widget = QtWidgets.QWidget()
        self.layouts.right_layout.addWidget(content_widget)

        settings_v_lay = QtWidgets.QVBoxLayout(content_widget)
        header_layout = QtWidgets.QVBoxLayout()
        settings_v_lay.addLayout(header_layout)

        # add the title
        title_label = HeaderLabel("Change User Password")
        header_layout.addWidget(title_label)

        # add a label to show the path of the settings file
        path_label = ResolvedText(
            f"Change user password of {self.main_object.user.name}"
        )
        header_layout.addWidget(path_label)
        header_layout.addWidget(VerticalSeparator(color=(255, 141, 28), height=1))

        # form layout
        form_layout = QtWidgets.QFormLayout()
        settings_v_lay.addLayout(form_layout)

        old_password_lbl = QtWidgets.QLabel("Old Password :")
        old_password_le = ValidatedString(
            name="old_password", allow_special_characters=True
        )
        old_password_le.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow(old_password_lbl, old_password_le)

        new_password_lbl = QtWidgets.QLabel("New Password :")
        new_password_le = ValidatedString(
            name="new_password", allow_special_characters=True
        )
        new_password_le.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow(new_password_lbl, new_password_le)

        new_password2_lbl = QtWidgets.QLabel("New Password Again :")
        new_password2_le = ValidatedString(
            name="new_password2", allow_special_characters=True
        )
        new_password2_le.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow(new_password2_lbl, new_password2_le)

        # add a button to change the password
        change_password_button = TikButton(text="Change Password", parent=self)
        settings_v_lay.addWidget(change_password_button)

        settings_v_lay.addStretch()

        def on_change_password():
            """Convenience function to change the password."""
            if new_password_le.text() != new_password2_le.text():
                self.feedback.pop_info(
                    title="Cannot change password",
                    text="New passwords do not match.",
                    critical=True,
                )
                return
            result, msg = self.main_object.user.change_user_password(
                old_password=old_password_le.text(),
                new_password=new_password_le.text(),
            )
            if result == -1:
                self.feedback.pop_info(
                    title="Cannot change password", text=msg, critical=True
                )
            else:
                self.feedback.pop_info(title="Password Changed", text=msg)
                old_password_le.clear()
                new_password_le.clear()
                new_password2_le.clear()
            self.error_count += 1

            if self.error_count == 2:
                self.feedback.pop_info(
                    title="Too many errors",
                    text=f"Friendly reminder: You are trying to change the password for:\n\n {self.main_object.user.name}.",
                )

            if self.error_count == 5:
                self.feedback.pop_info(
                    title="Too many errors",
                    text="This starting to look suspicious. I am watching you!",
                )

            if self.error_count == 12:
                self.feedback.pop_info(
                    title="Too many errors",
                    text="This is your last warning.",
                )

            if self.error_count > 12:
                self.feedback.pop_info(
                    title="Too many errors",
                    text="Thats it. Something fishy going on here. I am closing the window!",
                )
                self.close()

        # SIGNALS
        change_password_button.clicked.connect(on_change_password)

        content_widget.setVisible(False)
        return content_widget

    def project_title(self):
        """Create the project settings."""
        # create the menu items
        project_widget_item = SwitchTreeItem(["Project"], permission_level=3)
        self.menu_tree_widget.addTopLevelItem(project_widget_item)

        # create sub-branches
        preview_settings_item = SwitchTreeItem(["Preview Settings"], permission_level=3)
        project_widget_item.addChild(preview_settings_item)
        preview_settings_item.content = self.__create_generic_settings_layout(
            settings_data=self.main_object.project.preview_settings,
            title="Preview Settings",
        )
        category_definitions = SwitchTreeItem(
            ["Category Definitions"], permission_level=3
        )
        project_widget_item.addChild(category_definitions)
        category_definitions.content = self._project_category_definitions_content()

        metadata = SwitchTreeItem(["Metadata"], permission_level=3)
        project_widget_item.addChild(metadata)
        metadata.content = self._metadata_content()

        # project_settings = SwitchTreeItem(["Project Settings"], permission_level=3)
        # project_widget_item.addChild(project_settings)

    def common_title(self):
        """Create the common settings."""
        # create the menu items
        common_widget_item = SwitchTreeItem(["Common"], permission_level=3)
        self.menu_tree_widget.addTopLevelItem(common_widget_item)

        # create sub-branches
        category_definitions = SwitchTreeItem(
            ["Category Definitions (Common)"], permission_level=3
        )
        common_widget_item.addChild(category_definitions)
        category_definitions.content = self._common_category_definitions_content()

        metadata = SwitchTreeItem(["Metadata (Common)"], permission_level=3)
        common_widget_item.addChild(metadata)
        metadata.content = self._common_metadata_content()

        users_management = SwitchTreeItem(["Users Management"], permission_level=3)
        common_widget_item.addChild(users_management)
        users_management.content = self.__common_users_management_content()

        # combine the ui definitions for all management platforms
        ui_definition = {}
        for plt in management.platforms.keys():
            settings_ui = management.platforms[plt].get_settings_ui()
            # update the management settings for any missing keys
            settings_data = convert_to_settings_data(settings_ui)
            self.main_object.user.commons.management_settings.add_missing_keys(settings_data)
            ui_definition.update(settings_ui)

        # ui_definition = management.platforms["shotgrid"].get_settings_ui()
        platform_settings = SwitchTreeItem(["Platform Settings"], permission_level=3)
        common_widget_item.addChild(platform_settings)
        platform_settings.content = self.__create_generic_settings_layout(
            settings_data=self.main_object.user.commons.management_settings,
            title="Platform Settings",
            ui_definition=ui_definition,
        )

    def create_content_links(self):
        """Create content widgets for all top level items."""
        # collect all root items
        root_items = [
            self.menu_tree_widget.topLevelItem(x)
            for x in range(self.menu_tree_widget.topLevelItemCount())
        ]
        for root_item in root_items:
            # create a content widget
            if not root_item.content:
                content_widget = QtWidgets.QWidget()
                content_widget.setVisible(False)
                content_layout = QtWidgets.QVBoxLayout(content_widget)
            else:
                content_widget = root_item.content
                content_layout = content_widget.layout()

            # get all children of the root item
            children = [root_item.child(x) for x in range(root_item.childCount())]
            for child in children:
                # create a QCommandLinkButton for each child
                button = QtWidgets.QCommandLinkButton(child.text(0))
                button.clicked.connect(
                    lambda _=None, x=child: self.menu_tree_widget.setCurrentItem(x)
                )
                content_layout.addWidget(button)

            content_layout.addStretch()
            self.layouts.right_layout.addWidget(content_widget)
            # add it to the item
            root_item.content = content_widget

    def apply_settings(self, close_dialog=False):
        """Apply the settings."""
        for settings_object in self.settings_list:
            settings_object.apply_settings()
            self.check_changes()
        if close_dialog:
            self.close()

    def check_changes(self):
        """Check if there are changes in the settings and enable the apply button."""

        for settings_object in self.settings_list:
            if settings_object.is_settings_changed():
                self.apply_button.setEnabled(True)
                return
        self.apply_button.setEnabled(False)

    def _gather_validations_and_extracts(self):
        """Collect the available validations and extracts."""
        if self._validations_and_extracts:
            return self._validations_and_extracts
        # we cannot simply rely on the collected validators and extractors due to it will
        # differ from Dcc to Dcc. So we need to collect them from the directories.
        # This method is not the best way to do it but it is the most reliable way.
        validations = []
        extracts = []

        is_frozen = getattr(sys, "frozen", False)
        # get the location of the file
        if not is_frozen:
            # get the location of the file. tik_manager/ui/dialog/settings_dialog.py
            _file_path = Path(__file__)
            tik_manager4_path = _file_path.parents[2]
        else:
            # First get the location of the executable
            # which is in by default tik_manager4/dist/tik4/<name>.exe
            _exe_path = Path(sys.executable)
            # Pick walk up to the tik_manager4 folder. This will be different if the executable is somewhere else.
            tik_manager4_path = _exe_path.parents[2]

        # DCC folder
        _dcc_folder = tik_manager4_path / "dcc"
        # collect all 'extract' and 'validate' folders under _dcc_folder recursively
        extract_folders = list(_dcc_folder.glob("**/extract"))
        validate_folders = list(_dcc_folder.glob("**/validate"))
        # collect all extractors
        for _extract_folder in extract_folders:
            extracts.extend(
                [
                    x.stem
                    for x in _extract_folder.glob("*.py")
                    if not x.stem.startswith("_")
                ]
            )
        for _validate_folder in validate_folders:
            validations.extend(
                [
                    x.stem
                    for x in _validate_folder.glob("*.py")
                    if not x.stem.startswith("_")
                ]
            )

        self._validations_and_extracts = {
            "validations": list(set(validations)),
            "extracts": list(set(extracts)),
        }
        return self._validations_and_extracts

    def __create_generic_settings_layout(
        self, settings_data, title="", ui_definition=None
    ):
        """Create a generic settings layout."""
        content_widget = QtWidgets.QWidget()
        self.layouts.right_layout.addWidget(content_widget)

        settings_v_lay = QtWidgets.QVBoxLayout(content_widget)

        header_layout = QtWidgets.QVBoxLayout()
        settings_v_lay.addLayout(header_layout)

        # add the title
        title_label = HeaderLabel(title)
        header_layout.addWidget(title_label)

        # add a label to show the path of the settings file
        path_label = ResolvedText(settings_data.settings_file)
        header_layout.addWidget(path_label)
        header_layout.addWidget(VerticalSeparator(color=(255, 141, 28), height=1))

        # make a scroll area for the main content
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_contents_widget = QtWidgets.QWidget()
        scroll_area_contents_widget.setGeometry(QtCore.QRect(0, 0, 104, 345))
        scroll_area.setWidget(scroll_area_contents_widget)
        settings_v_lay.addWidget(scroll_area)
        scroll_layout = QtWidgets.QVBoxLayout(scroll_area_contents_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Actual content creation begins here..
        self.settings_list.append(settings_data)
        ui_definition = ui_definition or convert_to_ui_definition(
            settings_data.properties
        )
        settings_layout = SettingsLayout(ui_definition, settings_data, parent=self)
        scroll_layout.addLayout(settings_layout)

        # SIGNALS
        settings_layout.modified.connect(self.check_changes)

        content_widget.setVisible(False)
        return content_widget

    def _project_category_definitions_content(self):
        """Create the project category definitions."""

        settings_data = self.main_object.project.guard.category_definitions
        availability_dict = self._gather_validations_and_extracts()
        self.settings_list.append(settings_data)

        project_category_definitions_widget = CategoryDefinitions(
            settings_data,
            availability_dict,
            title="Category Definitions (Project)",
            parent=self,
        )

        # hide by default
        project_category_definitions_widget.setVisible(False)
        self.layouts.right_layout.addWidget(project_category_definitions_widget)

        # SIGNALS
        project_category_definitions_widget.modified.connect(self.check_changes)
        return project_category_definitions_widget

    def _metadata_content(self):
        """Create the metadata content."""
        settings_data = self.main_object.project.metadata_definitions
        # add it to the global settings list so it can be checked globally.
        self.settings_list.append(settings_data)

        metadata_widget = MetadataDefinitions(
            settings_data, title="Metadata Definitions", parent=self
        )
        metadata_widget.setVisible(False)
        self.layouts.right_layout.addWidget(metadata_widget)

        # SIGNALS
        metadata_widget.modified.connect(self.check_changes)
        return metadata_widget

    def _common_metadata_content(self):
        """Create the common metadata content."""
        settings_data = self.main_object.user.commons.metadata
        # add it to the global settings list so it can be checked globally.
        self.settings_list.append(settings_data)

        common_metadata_widget = MetadataDefinitions(
            settings_data, title="Metadata Definitions (Common)", parent=self
        )
        common_metadata_widget.setVisible(False)
        self.layouts.right_layout.addWidget(common_metadata_widget)

        # SIGNALS
        common_metadata_widget.modified.connect(self.check_changes)
        return common_metadata_widget

    def _common_category_definitions_content(self):
        """Create the common category definitions."""
        settings_data = self.main_object.user.commons.category_definitions
        availability_dict = self._gather_validations_and_extracts()
        self.settings_list.append(settings_data)

        common_category_definitions_widget = CategoryDefinitions(
            settings_data,
            availability_dict,
            title="Category Definitions (Common)",
            parent=self,
        )
        common_category_definitions_widget.setVisible(False)
        self.layouts.right_layout.addWidget(common_category_definitions_widget)

        # SIGNALS
        common_category_definitions_widget.modified.connect(self.check_changes)
        return common_category_definitions_widget

    def __common_users_management_content(self):
        """Create the user management content."""
        settings_data = self.main_object.user.commons.users
        # add the settings data so it can be checked for alterations within the entire dialog
        self.settings_list.append(settings_data)

        user_management_widget = UsersDefinitions(
            self.main_object.user, title="Users Management", parent=self
        )
        user_management_widget.setVisible(False)  # hide by default
        self.layouts.right_layout.addWidget(user_management_widget)

        # SIGNALS
        user_management_widget.modified.connect(self.check_changes)
        return user_management_widget


class UsersDefinitions(QtWidgets.QWidget):
    """Widget for users definitions management."""

    value_widgets = {
        "combo": value_widgets.Combo,
        "string": value_widgets.String,
    }

    modified = QtCore.Signal(bool)

    def __init__(self, user_object, *args, title="", **kwargs):
        """Initiate the class."""
        super().__init__(*args, **kwargs)
        self.title = title
        self.user_object = user_object
        self.settings_data = user_object.commons.users
        self.feedback = Feedback(parent=self)
        self.layouts = MainLayout()
        self.switch_tree_widget = None
        self.build_layouts()
        self.build_static_widgets()
        self.build_value_widgets()
        self.layouts.splitter.setSizes([500, 500])

    def build_layouts(self):
        """Build the layouts."""
        self.layouts.master_layout = QtWidgets.QVBoxLayout(self)
        self.layouts.header_layout = QtWidgets.QVBoxLayout()
        self.layouts.master_layout.addLayout(self.layouts.header_layout)

        self.layouts.splitter = QtWidgets.QSplitter(self)

        left_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.left_layout = QtWidgets.QVBoxLayout(left_widget)
        self.layouts.left_layout.setContentsMargins(0, 0, 0, 0)

        right_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.right_layout = QtWidgets.QVBoxLayout(right_widget)
        self.layouts.right_layout.setContentsMargins(0, 0, 0, 0)

        self.layouts.master_layout.addWidget(self.layouts.splitter)

    def build_static_widgets(self):
        """Build static widgets."""
        title_label = HeaderLabel(self.title)
        self.layouts.header_layout.addWidget(title_label)

        # add a label to show the path of the settings file
        path_label = ResolvedText(self.settings_data.settings_file)
        path_label.setMaximumHeight(30)
        self.layouts.header_layout.addWidget(path_label)

        self.layouts.header_layout.addWidget(
            VerticalSeparator(color=(255, 141, 28), height=1)
        )

        self.switch_tree_widget = SwitchTreeWidget()
        self.switch_tree_widget.setRootIsDecorated(False)
        self.switch_tree_widget.setHeaderHidden(True)
        self.switch_tree_widget.header().setVisible(False)
        self.layouts.left_layout.addWidget(self.switch_tree_widget)

        # add 'add' and 'remove' buttons in a horizontal layout
        add_remove_buttons_layout = QtWidgets.QHBoxLayout()
        self.layouts.left_layout.addLayout(add_remove_buttons_layout)
        add_metadata_button = TikButton(text="Add New User", parent=self)
        add_remove_buttons_layout.addWidget(add_metadata_button)
        remove_metadata_button = TikButton(text="Delete User", parent=self)
        add_remove_buttons_layout.addWidget(remove_metadata_button)

        # SIGNALS
        add_metadata_button.clicked.connect(self.add_user)
        remove_metadata_button.clicked.connect(self.remove_user)

    def reinit(self):
        """Reinitialize the widget."""
        self.switch_tree_widget.clear()
        self.build_value_widgets()

    def add_user(self):
        """Launch the add user dialog."""
        # refresh the switch tree widget
        dialog = NewUserDialog(self.user_object, parent=self)
        state = dialog.exec_()
        if state:
            self.reinit()

    def remove_user(self):
        """Remove the user from the database."""
        selected_item = self.switch_tree_widget.currentItem()
        if selected_item is None:
            return
        name = selected_item.text(0)
        are_you_sure = self.feedback.pop_question(
            title="Delete User",
            text=f"Are you sure you want to delete the user '{name}'? This action cannot be undone.",
            buttons=["yes", "cancel"],
        )
        if are_you_sure == "cancel":
            return

        result, msg = self.user_object.delete_user(name)
        if result == -1:
            self.feedback.pop_info(title="Cannot delete user", text=msg, critical=True)
            return
        self.reinit()

    def _delete_value_widget(self, widget_item):
        """Deletes the value widget and removes it from the layout."""
        widget_item.content.deleteLater()
        self.layouts.right_layout.removeWidget(widget_item.content)
        widget_item.content = None

    def _add_value_widget(self, name, data):
        """Add a new value widget to the layout."""
        # create the widget item
        widget_item = SwitchTreeItem([name])
        self.switch_tree_widget.addTopLevelItem(widget_item)

        # create the content widget
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout()
        content_widget.setLayout(content_layout)

        form_layout = QtWidgets.QFormLayout()
        content_layout.addLayout(form_layout)
        # type label. We don't want to make it editable.
        # Easier to delete the metadata and add a new one.
        type_name = ResolvedText(data["initials"])
        form_layout.addRow("Initials: ", type_name)

        user_email = ValidatedString(name="user_email", value=data.get("email", ""), allow_special_characters=True)

        form_layout.addRow("Email: ", user_email)

        # Parse the value to the string
        permission_levels = ["Observer", "Generic", "Experienced", "Admin"]
        permission_as_string = permission_levels[data["permissionLevel"]]

        permission_widget = self.value_widgets["combo"](
            name="permissionLevel", value=permission_as_string, items=permission_levels
        )
        # if this is default Admin user, make it uneditable
        if name == "Admin":
            permission_widget.setEnabled(False)

        form_layout.addRow("Permission Level: ", permission_widget)
        permission_widget.currentIndexChanged.connect(
            lambda value: data.update({"permissionLevel": value})
        )
        permission_widget.com.valueChanged.connect(
            lambda value: self.modified.emit(True)
        )

        # user_email.com.valueChanged.connect(lambda value: self.modified.emit(True))
        user_email.textChanged.connect(lambda value: data.update({"email": value}))
        user_email.com.valueChanged.connect(lambda value: self.modified.emit(True))

        content_widget.setVisible(False)
        self.layouts.right_layout.addWidget(content_widget)
        widget_item.content = content_widget

    def build_value_widgets(self):
        """Build the widgets."""

        for metadata_key, data in self.settings_data.properties.items():
            self._add_value_widget(metadata_key, data)


class MetadataDefinitions(QtWidgets.QWidget):
    """Widget for metadata definitions management."""

    value_widgets = {
        "boolean": value_widgets.Boolean,
        "string": value_widgets.String,
        "integer": value_widgets.Integer,
        "float": value_widgets.Float,
        "vector2Int": value_widgets.Vector2Int,
        "vector2Float": value_widgets.Vector2Float,
        "vector3Int": value_widgets.Vector3Int,
        "vector3Float": value_widgets.Vector3Float,
        "combo": value_widgets.Combo,
    }

    modified = QtCore.Signal(bool)

    def __init__(self, settings_data, *args, title="", **kwargs):
        super().__init__(*args, **kwargs)

        # variables
        self.title = title
        self.settings_data = settings_data

        self.layouts = MainLayout()
        self.switch_tree_widget = None

        self.build_layouts()
        self.build_static_widgets()
        self.build_value_widgets()

        self.layouts.splitter.setSizes([500, 500])

    def build_layouts(self):
        """Build the layouts."""
        self.layouts.master_layout = QtWidgets.QVBoxLayout(self)
        self.layouts.header_layout = QtWidgets.QVBoxLayout()
        self.layouts.master_layout.addLayout(self.layouts.header_layout)

        self.layouts.splitter = QtWidgets.QSplitter(self)

        left_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.left_layout = QtWidgets.QVBoxLayout(left_widget)
        self.layouts.left_layout.setContentsMargins(0, 0, 0, 0)

        right_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.right_layout = QtWidgets.QVBoxLayout(right_widget)
        self.layouts.right_layout.setContentsMargins(0, 0, 0, 0)

        self.layouts.master_layout.addWidget(self.layouts.splitter)

    def build_static_widgets(self):
        """Build static widgets."""
        title_label = HeaderLabel(self.title)
        self.layouts.header_layout.addWidget(title_label)

        # add a label to show the path of the settings file
        path_label = ResolvedText(self.settings_data.settings_file)
        path_label.setMaximumHeight(30)
        self.layouts.header_layout.addWidget(path_label)

        self.layouts.header_layout.addWidget(
            VerticalSeparator(color=(255, 141, 28), height=1)
        )

        self.switch_tree_widget = SwitchTreeWidget()
        self.switch_tree_widget.setRootIsDecorated(False)
        self.switch_tree_widget.setHeaderHidden(True)
        self.switch_tree_widget.header().setVisible(False)
        self.layouts.left_layout.addWidget(self.switch_tree_widget)

        # add 'add' and 'remove' buttons in a horizontal layout
        add_remove_buttons_layout = QtWidgets.QHBoxLayout()
        self.layouts.left_layout.addLayout(add_remove_buttons_layout)
        add_metadata_button = TikButton(text="Add New Metadata", parent=self)
        add_remove_buttons_layout.addWidget(add_metadata_button)
        remove_metadata_button = TikButton(text="Delete Metadata", parent=self)
        add_remove_buttons_layout.addWidget(remove_metadata_button)

        # SIGNALS
        add_metadata_button.clicked.connect(self.add_metadata)
        remove_metadata_button.clicked.connect(self.remove_metadata)

    def add_metadata(self):
        """Pop up a dialog to add a new metadata."""
        _dialog = QtWidgets.QDialog(self)
        _dialog.setWindowTitle("Add Metadata")
        dialog_layout = QtWidgets.QVBoxLayout(_dialog)
        _dialog.setLayout(dialog_layout)
        # create a combo box to select the type
        type_combo = QtWidgets.QComboBox(self)
        type_combo.addItems(list(self.value_widgets.keys()))
        dialog_layout.addWidget(type_combo)
        # create a line edit to enter the name
        name_line_edit = QtWidgets.QLineEdit(self)
        dialog_layout.addWidget(name_line_edit)
        # create a button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        dialog_layout.addWidget(button_box)
        # if user clicks ok return the selected items
        button_box.accepted.connect(_dialog.accept)
        button_box.rejected.connect(_dialog.reject)
        # show the dialog
        _dialog.show()
        # if user accepts the dialog, add the metadata
        if _dialog.exec_():
            name = name_line_edit.text()
            data_type = type_combo.currentText()
            default_data = self._prepare_default_data(data_type)
            self.settings_data.add_property(name, default_data)
            self._add_value_widget(name, data=default_data)
            # emit the modified signal
            self.modified.emit(True)

    @staticmethod
    def _prepare_default_data(data_type):
        """Convenience method to prepare the default data for the given data type."""

        if data_type == "boolean":
            _default_object_type: bool = False
        elif data_type == "string":
            _default_object_type: str = ""
        elif data_type == "integer":
            _default_object_type: int = 0
        elif data_type == "float":
            _default_object_type: float = 0.0
        elif data_type == "vector2Int":
            _default_object_type: list = [0, 0]
        elif data_type == "vector2Float":
            _default_object_type: list = [0.0, 0.0]
        elif data_type == "vector3Int":
            _default_object_type: list = [0, 0, 0]
        elif data_type == "vector3Float":
            _default_object_type: list = [0.0, 0.0, 0.0]
        elif data_type == "combo":
            _default_object_type: str = ""
        else:
            _default_object_type: str = ""
        default_data = {"default": _default_object_type, "type": data_type}
        # enum lists are only for combo boxes
        if data_type == "combo":
            default_data["enum"] = []
        return default_data

    def remove_metadata(self):
        """Removes the selected metadata from the layout."""
        # get the selected item
        selected_item = self.switch_tree_widget.currentItem()
        if selected_item is None:
            return
        # get the name of the metadata
        name = selected_item.text(0)
        # delete it from the tree widget
        self.switch_tree_widget.takeTopLevelItem(
            self.switch_tree_widget.indexOfTopLevelItem(selected_item)
        )
        # delete the value widget
        self._delete_value_widget(selected_item)
        # delete the metadata from the settings
        self.settings_data.delete_property(name)
        # emit the modified signal
        self.modified.emit(True)

    def _delete_value_widget(self, widget_item):
        """Deletes the value widget and removes it from the layout."""
        widget_item.content.deleteLater()
        self.layouts.right_layout.removeWidget(widget_item.content)
        widget_item.content = None

    def _add_value_widget(self, name, data):
        """Add a new value widget to the layout."""
        # create the widget item
        widget_item = SwitchTreeItem([name])
        self.switch_tree_widget.addTopLevelItem(widget_item)

        # create the content widget
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout()
        content_widget.setLayout(content_layout)

        # guess the data type from its default value
        # if there is an enum list, that means it is a combo box
        data_type = data.get("type", guess_data_type(data["default"]))

        form_layout = QtWidgets.QFormLayout()
        content_layout.addLayout(form_layout)
        # type label. We don't want to make it editable.
        # Easier to delete the metadata and add a new one.
        type_label = QtWidgets.QLabel("Type: ")
        type_name = ResolvedText(data_type)
        form_layout.addRow(type_label, type_name)

        # default value
        default_value_label = QtWidgets.QLabel("Default Value: ")
        default_value_widget = self.value_widgets[data_type](
            name="default_value", value=data["default"]
        )
        form_layout.addRow(default_value_label, default_value_widget)
        default_value_widget.com.valueChanged.connect(
            lambda value: data.update({"default": value})
        )
        default_value_widget.com.valueChanged.connect(
            lambda value: self.modified.emit(True)
        )

        # create an additional list widget for combo items
        if data_type == "combo":
            combo_items_label = QtWidgets.QLabel("Combo Items: ")
            combo_items_widget = value_widgets.List(name="enum", value=data["enum"])
            default_value_widget.addItems(data["enum"])
            default_value_widget.setCurrentText(data["default"])
            form_layout.addRow(combo_items_label, combo_items_widget)
            combo_items_widget.com.valueChanged.connect(
                lambda value: data.update({"enum": value})
            )
            combo_items_widget.com.valueChanged.connect(
                lambda value: self.modified.emit(True)
            )

        content_widget.setVisible(False)
        self.layouts.right_layout.addWidget(content_widget)
        widget_item.content = content_widget

    def build_value_widgets(self):
        """Build the widgets."""

        for metadata_key, data in self.settings_data.properties.items():
            self._add_value_widget(metadata_key, data)


class CategoryDefinitions(QtWidgets.QWidget):
    """Widget for category definitions management."""

    modified = QtCore.Signal(bool)

    def __init__(self, settings_data, availability_dict, *args, title="", **kwargs):
        """Initiate the class."""
        super().__init__(*args, **kwargs)
        self.availability_dict = availability_dict

        self.title = title
        self.settings_data = settings_data

        self.layouts = MainLayout()

        self.switch_tree_widget = None

        self.build_layouts()
        self.build_static_widgets()
        self.build_value_widgets()

        self.layouts.splitter.setSizes([500, 500])

    def build_layouts(self):
        """Build the layouts."""
        self.layouts.master_layout = QtWidgets.QVBoxLayout(self)
        self.layouts.header_layout = QtWidgets.QVBoxLayout()
        self.layouts.master_layout.addLayout(self.layouts.header_layout)

        self.layouts.splitter = QtWidgets.QSplitter(self)

        left_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.left_layout = QtWidgets.QVBoxLayout(left_widget)
        self.layouts.left_layout.setContentsMargins(0, 0, 0, 0)

        right_widget = QtWidgets.QWidget(self.layouts.splitter)
        self.layouts.right_layout = QtWidgets.QVBoxLayout(right_widget)
        self.layouts.right_layout.setContentsMargins(0, 0, 0, 0)

        self.layouts.master_layout.addWidget(self.layouts.splitter)

    def build_static_widgets(self):
        """Build static widgets."""
        title_label = HeaderLabel(self.title)
        # title_label.setMaximumHeight(30)
        self.layouts.header_layout.addWidget(title_label)

        # add a label to show the path of the settings file
        path_label = ResolvedText(self.settings_data.settings_file)
        path_label.setMaximumHeight(30)
        self.layouts.header_layout.addWidget(path_label)

        self.layouts.header_layout.addWidget(
            VerticalSeparator(color=(255, 141, 28), height=1)
        )

        self.switch_tree_widget = SwitchTreeWidget()
        self.switch_tree_widget.setRootIsDecorated(False)
        self.switch_tree_widget.setHeaderHidden(True)
        self.switch_tree_widget.header().setVisible(False)
        self.layouts.left_layout.addWidget(self.switch_tree_widget)

        # add 'add' and 'remove' buttons in a horizontal layout
        add_remove_buttons_layout = QtWidgets.QHBoxLayout()
        self.layouts.left_layout.addLayout(add_remove_buttons_layout)
        add_category_pb = TikButton(text="Add New Category", parent=self)
        add_remove_buttons_layout.addWidget(add_category_pb)
        delete_category_pb = TikButton(text="Delete Category", parent=self)
        add_remove_buttons_layout.addWidget(delete_category_pb)

        # SIGNALS
        add_category_pb.clicked.connect(self.add_category)
        delete_category_pb.clicked.connect(self.delete_category)

    def add_category(self):
        """Pop up a dialog to add a new category."""

        def _add_category_item():
            name = name_line_edit.text()
            if name in self.settings_data.properties:
                if self.settings_data.get_property(name).get("archived", False):
                    self.settings_data.edit_sub_property((name, "archived"), False)
                    self._add_value_widget(
                        name, data=self.settings_data.get_property(name)
                    )
                    # emit the modified signal
                    self.modified.emit(True)
                    add_category_dialog.close()
                    return
                QtWidgets.QMessageBox.warning(
                    self,
                    "Warning",
                    f"Category with the name '{name}' already exists.",
                )
                return
            default_data = {
                "type": "",
                "validations": [],
                "extracts": [],
            }
            self.settings_data.add_property(name, default_data)
            self._add_value_widget(name, data=default_data)
            # emit the modified signal
            self.modified.emit(True)
            add_category_dialog.close()

        add_category_dialog = QtWidgets.QDialog(self)
        add_category_dialog.setWindowTitle("Add Category")
        dialog_layout = QtWidgets.QVBoxLayout(add_category_dialog)
        add_category_dialog.setLayout(dialog_layout)
        # create a line edit to enter the name
        horizontal_layout = QtWidgets.QHBoxLayout()
        dialog_layout.addLayout(horizontal_layout)
        name_label = QtWidgets.QLabel("Name: ")
        name_line_edit = ValidatedString("name")
        name_line_edit.allow_spaces = False
        name_line_edit.allow_special_characters = False
        name_line_edit.allow_empty = False
        horizontal_layout.addWidget(name_label)
        horizontal_layout.addWidget(name_line_edit)
        # create a button box
        button_box = TikButtonBox()
        add_category_pb = button_box.addButton(
            "Add", QtWidgets.QDialogButtonBox.AcceptRole
        )
        name_line_edit.set_connected_widgets(add_category_pb)
        _cancel_pb = button_box.addButton(
            "Cancel", QtWidgets.QDialogButtonBox.RejectRole
        )
        dialog_layout.addWidget(button_box)
        # if user clicks ok return the selected items
        # button_box.accepted.connect(add_category_dialog.accept)
        add_category_pb.clicked.connect(_add_category_item)
        button_box.rejected.connect(add_category_dialog.reject)
        # show the dialog
        add_category_dialog.show()

    def delete_category(self):
        """Removes the selected category from the layout."""
        # get the selected item
        selected_item = self.switch_tree_widget.currentItem()
        if selected_item is None:
            return
        # get the name of the metadata
        category_name = selected_item.text(0)
        # delete it from the tree widget
        self.switch_tree_widget.takeTopLevelItem(
            self.switch_tree_widget.indexOfTopLevelItem(selected_item)
        )
        # delete the value widget
        self._delete_value_widget(selected_item)
        # ARCHIVE the category in settings data
        self.settings_data.edit_sub_property((category_name, "archived"), True)
        # emit the modified signal
        self.modified.emit(True)

    def _delete_value_widget(self, widget_item):
        """Deletes the value widget and removes it from the layout."""
        widget_item.content.deleteLater()
        self.layouts.right_layout.removeWidget(widget_item.content)
        widget_item.content = None

    def __add_type(self, form_layout, data):
        """Convenience method for adding a type widget."""
        type_label = QtWidgets.QLabel("Type: ")
        type_combo = value_widgets.Combo(name="type", value=data["type"])
        type_combo.setToolTip(
            "Type of the category. "
            "This value defines if the category belongs to an asset or shot mode. "
            "If left empty, it will be available in all modes."
        )
        type_combo.addItems(["asset", "shot", ""])
        type_combo.setCurrentText(data["type"])

        form_layout.addRow(type_label, type_combo)

        # SIGNALS
        type_combo.com.valueChanged.connect(lambda value: data.update({"type": value}))
        type_combo.com.valueChanged.connect(lambda value: self.modified.emit(True))

    def __add_validations(self, form_layout, data):
        """Convenience method for adding validations view."""
        validations_layout = QtWidgets.QHBoxLayout()
        validations_label = QtWidgets.QLabel("Validations: ")
        # create a standard model to hold and manipulate the data
        validations_model = ReorderListModel()
        validations_model.setStringList(data["validations"])
        validations_list = QtWidgets.QListView()
        # validations_list = ReorderListView()
        validations_list.setModel(validations_model)
        # # make the items in the list change order by drag and drop
        validations_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        # make it multi selection
        validations_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        validations_layout.addWidget(validations_list)
        # add the buttons
        validations_buttons_layout = QtWidgets.QVBoxLayout()
        validations_layout.addLayout(validations_buttons_layout)
        add_validation_button = TikIconButton(
            icon_name="plus", size=32, background_color="#405040", parent=self
        )
        validations_buttons_layout.addWidget(add_validation_button)
        remove_validation_button = TikIconButton(
            icon_name="minus", size=32, parent=self, background_color="#504040"
        )

        validations_buttons_layout.addWidget(remove_validation_button)

        form_layout.addRow(validations_label, validations_layout)

        # SIGNALS
        validations_list.model().rowsMoved.connect(
            lambda _: self._reorder_items(validations_model, data["validations"])
        )
        remove_validation_button.clicked.connect(
            lambda: self._remove_item(
                validations_model, validations_list, data["validations"]
            )
        )
        add_validation_button.clicked.connect(
            lambda: self._add_item(
                validations_model, data["validations"], "validations"
            )
        )

    def __add_extracts(self, form_layout, data):
        """Convenience method to add extracts view."""
        extracts_layout = QtWidgets.QHBoxLayout()
        extracts_label = QtWidgets.QLabel("Extracts: ")
        # create a standard model to hold and manipulate the data
        extracts_model = QtCore.QStringListModel()
        extracts_model.setStringList(data["extracts"])
        extracts_list = QtWidgets.QListView()
        extracts_list.setModel(extracts_model)
        extracts_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        extracts_layout.addWidget(extracts_list)
        # add the buttons
        extracts_buttons_layout = QtWidgets.QVBoxLayout()
        extracts_layout.addLayout(extracts_buttons_layout)
        add_extract_button = TikIconButton(
            icon_name="plus", size=32, background_color="#405040", parent=self
        )
        extracts_buttons_layout.addWidget(add_extract_button)
        remove_extract_button = TikIconButton(
            icon_name="minus", size=32, parent=self, background_color="#504040"
        )
        extracts_buttons_layout.addWidget(remove_extract_button)

        form_layout.addRow(extracts_label, extracts_layout)

        # SIGNALS
        extracts_list.model().rowsMoved.connect(
            lambda _: self._reorder_items(extracts_model, data["extracts"])
        )
        remove_extract_button.clicked.connect(
            lambda: self._remove_item(extracts_model, extracts_list, data["extracts"])
        )
        add_extract_button.clicked.connect(
            lambda: self._add_item(extracts_model, data["extracts"], "extracts")
        )

    def _add_value_widget(self, name, data):
        """Adds a new value widget to the layout."""

        # if it is archived, skip it.
        if data.get("archived"):
            return

        widget_item = SwitchTreeItem([name])
        self.switch_tree_widget.addTopLevelItem(widget_item)

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout()
        content_widget.setLayout(content_layout)

        form_layout = QtWidgets.QFormLayout()
        content_layout.addLayout(form_layout)

        # add type, validations and extracts
        self.__add_type(form_layout, data)
        self.__add_validations(form_layout, data)
        self.__add_extracts(form_layout, data)

        # link the content widget to the item for visibility switching
        content_widget.setVisible(False)
        self.layouts.right_layout.addWidget(content_widget)
        widget_item.content = content_widget

    def _remove_item(self, validations_model, validations_list, list_data):
        """Removes the selected item from the list view."""
        # validations_model.removeRow(validations_list.currentIndex().row())
        selected_index = validations_list.currentIndex().row()
        if selected_index == -1:
            return
        # sorting and reversing the indexes to avoid index errors
        for index in reversed(sorted(validations_list.selectedIndexes())):
            selected_index = index.row()
            # Remove the item from the underlying data
            list_data.pop(selected_index)
            # Update the model
            validations_model.removeRow(selected_index)
            self.modified.emit(True)

    def _add_item(self, model, list_data, list_type):
        """Pops up a mini dialog to add the item to the list view."""
        # Make a dialog with a listwidget to select the ifem(s) to add
        add_item_dialog = QtWidgets.QDialog(self)
        add_item_dialog.setWindowTitle("Add Item")
        dialog_layout = QtWidgets.QVBoxLayout(add_item_dialog)
        list_widget = QtWidgets.QListWidget()
        available_items = [
            x for x in self.availability_dict[list_type] if x not in list_data
        ]
        list_widget.addItems(available_items)
        # make it multi selection
        list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        dialog_layout.addWidget(list_widget)
        button_layout = QtWidgets.QHBoxLayout()
        # create the buttons with button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )

        def add():
            for item in list_widget.selectedItems():
                model.insertRow(model.rowCount())
                model.setData(model.index(model.rowCount() - 1), item.text())
                list_data.append(item.text())
                self.modified.emit(True)
            add_item_dialog.accept()

        # if user clicks ok return the selected items
        button_box.accepted.connect(add)
        button_box.rejected.connect(add_item_dialog.reject)
        button_layout.addWidget(button_box)
        dialog_layout.addLayout(button_layout)
        add_item_dialog.show()

    def _reorder_items(self, validations_model, list_data):
        """Update the model with re-ordered items."""
        for idx, item in enumerate(validations_model.stringList()):
            list_data[idx] = item
        self.modified.emit(True)

    def build_value_widgets(self):
        """Build the widgets."""
        # _valid_types = list(self.value_widgets.keys())
        for metadata_key, data in self.settings_data.properties.items():
            self._add_value_widget(metadata_key, data)


class ReorderListModel(QtCore.QStringListModel):
    """Custom QStringListModel that disables the overwrite
    when reordering items by drag and drop.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, strings=None, parent=None):
        super().__init__(parent)
        if strings is not None:
            self.setStringList(strings)

    def flags(self, index):
        """Override the flags method to disable the overwrite."""
        if index.isValid():
            return (
                QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsDragEnabled
                | QtCore.Qt.ItemIsEnabled
            )
        return (
            QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsDragEnabled
            | QtCore.Qt.ItemIsDropEnabled
            | QtCore.Qt.ItemIsEnabled
        )


# test the dialog
if __name__ == "__main__":
    import sys
    import tik_manager4
    from tik_manager4.ui import pick

    app = QtWidgets.QApplication(sys.argv)
    tik = tik_manager4.initialize("Standalone")
    _style_file = pick.style_file()
    dialog = SettingsDialog(tik, styleSheet=str(_style_file.readAll(), "utf-8"))
    dialog.show()
    sys.exit(app.exec_())
