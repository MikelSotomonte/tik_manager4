"""
NAME: 1-Tik4 Main UI
ICON: PATH/TO/PARENT/FOLDER/OF/TIKMANAGER4/tik_manager4/dcc/katana/setup/icons/tik4_main_ui.png
KEYBOARD_SHORTCUT:
SCOPE:
Enter Description Here

"""

# The following symbols are added when run as a shelf item script:
# exit():      Allows 'error-free' early exit from the script.
# console_print(message, raiseTab=False):
#              Prints the given message to the result area of the largest
#              available Python tab.
#              If raiseTab is passed as True, the tab will be raised to the
#              front in its pane.
#              If no Python tab exists, prints the message to the shell.
# console_clear(raiseTab=False):
#              Clears the result area of the largest available Python tab.
#              If raiseTab is passed as True, the tab will be raised to the
#              front in its pane.

from tik_manager4.ui import main as tik4_main
tik4_main.launch(dcc="Katana")
