import re
import os.path

import sublime
import sublime_plugin


platforms = {"osx": "OSX", "windows": "Windows", "linux": "Linux"}
PLATFORM = platforms.pop(sublime.platform())
IGNORED_PLATFORMS = "|".join(platforms.values())


class KindInputHandler(sublime_plugin.ListInputHandler):
    """Shows a list of configuration kinds to choose one as the 'kind' argument."""

    def placeholder(self):
        return "configurations"

    def list_items(self):
        return ["settings", "keymap", "mousemap", "menu"]

    def next_input(self, args):
        return BaseFileInputHandler(args["kind"])


class BaseFileInputHandler(sublime_plugin.ListInputHandler):
    """Shows a list of items to choose one as the 'base_file' argument."""

    PACKAGES = "${packages}/"

    # exclude user files and platform variants other than the current
    SETTINGS_RE = re.compile(r"Packages/("
                             r"(?!User)((?![^/]+$).+)/"  # package
                             r"([^(.]+(?:\((?!%s)[^).]+\))?)"  # name
                             r"\.sublime-settings)" % IGNORED_PLATFORMS)
    KEYMAP_RE = re.compile(r"Packages/("
                           r"(?!User)([^/]+)(?:(?![^/]+$).*)/"
                           r"Default(?: \((?!%s)[^).]+\))?"
                           r"\.sublime-keymap)" % IGNORED_PLATFORMS)
    MOUSEMAP_RE = re.compile(r"Packages/("
                             r"(?!User)([^/]+)(?:(?![^/]+$).*)/"
                             r"Default(?: \((?!%s)[^).]+\))?"
                             r"\.sublime-mousemap)" % IGNORED_PLATFORMS)
    MENU_RE = re.compile(r"Packages/("
                         r"(?!User)([^/]+)(?:(?![^/]+$).*)/"
                         r"([\w\s]+?)"
                         r"\.sublime-menu)")

    def __init__(self, kind):
        self.kind = kind

    def placeholder(self):
        return "File"

    def preview(self, value):
        """Show the full path in the preview area"""
        return value[12:]

    def list_items(self):

        if self.kind in ("keymap", "mousemap"):
            items = []
            pattern = self.KEYMAP_RE if self.kind == "keymap" else self.MOUSEMAP_RE
            for f in sublime.find_resources("*.sublime-" + self.kind):
                match = pattern.match(f)
                if not match:
                    continue
                path, name = match.groups()
                items.append((name, self.PACKAGES + path))
            return sorted(items)

        if self.kind == "settings":
            groups = []
            names = []
            for f in sublime.find_resources("*.sublime-settings"):
                match = self.SETTINGS_RE.match(f)
                if not match:
                    continue
                mg = match.groups()
                groups.append(mg)
                names.append(mg[2])

            # get repeated names
            for name in set(names):
                names.remove(name)
            repeated_names = set(names)

            # if there's more than one settings file with the same name show
            # their packages as hints.
            return sorted(("%s\t%s" % (name, pkg) if name in repeated_names else name,
                           self.PACKAGES + path)
                          for path, pkg, name in groups)

        if self.kind == "menu":
            items = []
            for f in sublime.find_resources("*.sublime-menu"):
                match = self.MENU_RE.match(f)
                if not match:
                    continue
                path, pkg, name = match.groups()
                # show the menu's name as a hint (e.g Context, SideBar, ...)
                items.append(("%s\t%s" % (pkg, name), self.PACKAGES + path))
            return sorted(items)

        sublime.error_message('edit_settings:\n\nkind must be one of:'
                              '\n- "settings"\n- "keymap"\n- "menu"\n- "mousemap'
                              '\ngot ' + repr(self.kind))


class EditSettingsCommand(sublime_plugin.ApplicationCommand):

    def input(self, args):
        if "base_file" not in args:
            if "kind" not in args:
                return KindInputHandler()
            return BaseFileInputHandler(args["kind"])
        return None

    def input_description(self):
        return "Edit"

    def run(self, base_file, user_file=None, default=None, kind=None):
        """
        :param base_file:
            A unicode string of the path to the base settings file. Typically
            this will be in the form: "${packages}/PackageName/Package.sublime-settings"

        :param user_file:
            An optional file path to the user's editable version of the settings
            file. If not provided, the filename from base_file will be appended
            to "${packages}/User/".

        :param default:
            An optional unicode string of the default contents if the user
            version of the settings file does not yet exist. Use "$0" to place
            the cursor.

        :param kind:
            An optional unicode string that specifies what kind of files to list,
            takes one of "settings", "keymap", "mousemap" and "menu"
        """

        if base_file is None:
            raise ValueError("No base_file argument was passed to edit_settings")
        if default is None:
            if base_file.endswith("settings"):
                default = "{\n\t$0\n}"
            else:
                default = "[\n\t{\n\t\t$0\n\t}\n]"

        variables = {
            "packages": "${packages}",
            "platform": PLATFORM
        }

        base_file = sublime.expand_variables(base_file.replace("\\", "\\\\"), variables)
        if user_file is not None:
            user_file = sublime.expand_variables(user_file.replace("\\", "\\\\"), variables)

        base_path = base_file.replace("${packages}", "res://Packages")
        is_resource = base_path.startswith("res://")
        file_name = os.path.basename(base_file)
        resource_exists = is_resource and base_path[6:] in sublime.find_resources(file_name)
        filesystem_exists = (not is_resource) and os.path.exists(base_path)

        if not resource_exists and not filesystem_exists:
            sublime.error_message('The settings file "' + base_path + '" could not be opened')
            return

        if user_file is None:
            user_package_path = os.path.join(sublime.packages_path(), "User")
            user_file = os.path.join(user_package_path, file_name)

            # If the user path does not exist, and it is a supported
            # platform-variant file path, then try and non-platform-variant
            # file path.
            if not os.path.exists(os.path.join(user_package_path, file_name)):
                for suffix in (".sublime-keymap", ".sublime-mousemap", ".sublime-settings"):
                    platform_suffix = " (%s)%s" % (PLATFORM, suffix)
                    if not file_name.endswith(platform_suffix):
                        continue
                    non_platform_file_name = file_name[:-len(platform_suffix)] + suffix
                    non_platform_path = os.path.join(user_package_path, non_platform_file_name)
                    if os.path.exists(non_platform_path):
                        user_file = non_platform_path
                        break

        sublime.run_command("new_window")
        new_window = sublime.active_window()

        new_window.set_layout(
            {
                "cols": (0.0, 0.5, 1.0),
                "rows": (0.0, 1.0),
                "cells": ((0, 0, 1, 1), (1, 0, 2, 1))
            })
        new_window.focus_group(0)
        new_window.run_command('open_file', {'file': base_file})
        new_window.focus_group(1)
        new_window.run_command("open_file", {"file": user_file, "contents": default})

        new_window.set_tabs_visible(True)
        new_window.set_sidebar_visible(False)

        base_view = new_window.active_view_in_group(0)
        user_view = new_window.active_view_in_group(1)

        base_settings = base_view.settings()
        base_settings.set("edit_settings_view", "base")
        base_settings.set("edit_settings_other_view_id", user_view.id())

        user_settings = user_view.settings()
        user_settings.set("edit_settings_view", "user")
        user_settings.set("edit_settings_other_view_id", base_view.id())
        if not os.path.exists(user_file):
            user_view.set_scratch(True)
            user_settings.set("edit_settings_default", default.replace("$0", ""))


class EditSyntaxSettingsCommand(sublime_plugin.WindowCommand):
    """
    Opens the syntax-specific settings file for the currently active view
    """

    def run(self):
        view = self.window.active_view()
        syntax, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        self.window.run_command(
            'edit_settings',
            {
                'base_file': '${packages}/Default/Preferences.sublime-settings',
                'user_file': os.path.join(sublime.packages_path(), 'User', syntax + '.sublime-settings'),
                'default': (
                    '// These settings override both User and Default settings '
                    'for the %s syntax\n{\n\t$0\n}\n') % syntax
            })

    def is_enabled(self):
        return self.window.active_view() is not None


class EditSettingsListener(sublime_plugin.ViewEventListener):
    """
    Closes the base and user settings files together, and then closes the
    window if no other views are opened
    """

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('edit_settings_view') is not None

    def on_modified(self):
        """
        Prevents users from editing the base file
        """

        view_settings = self.view.settings()

        # If any edits are made to the user version, we unmark it as a
        # scratch view so that the user is prompted to save any changes
        if view_settings.get('edit_settings_view') == 'user' and self.view.is_scratch():
            file_region = sublime.Region(0, self.view.size())
            if view_settings.get('edit_settings_default') != self.view.substr(file_region):
                self.view.set_scratch(False)

    def on_pre_close(self):
        """
        Grabs the window id before the view is actually removed
        """

        if self.view.window() is None:
            return

        self.view.settings().set('window_id', self.view.window().id())

    def on_close(self):
        """
        Closes the other settings view when one of the two is closed
        """

        view_settings = self.view.settings()

        window_id = view_settings.get('window_id')
        window = None
        for win in sublime.windows():
            if win.id() == window_id:
                window = win
                break

        if not window:
            return

        other_view_id = view_settings.get('edit_settings_other_view_id')
        views = window.views()
        views_left = len(views)
        for other in views:
            if other.id() == other_view_id:
                window.focus_view(other)
                # Prevent the handler from running on the other view
                other.settings().erase('edit_settings_view')
                # Run after timeout so the UI doesn't block with the view half closed
                sublime.set_timeout(lambda: window.run_command("close"), 50)

        # Don't close the window if the user opens another view in the window
        # or adds a folder, since they likely didn't realize this is a settings
        # window
        if views_left == 1 and len(window.folders()) < 1:
            # If the user closes the window containing the settings views, and
            # this is not delayed, the close_window command will be run on any
            # other window that is open.
            def close_window():
                if window.id() == sublime.active_window().id():
                    window.run_command("close_window")
            sublime.set_timeout(close_window, 50)


class OpenFileSettingsCommand(sublime_plugin.WindowCommand):
    """
    Old syntax-specific settings command - preserved for backwards compatibility
    """

    def run(self):
        view = self.window.active_view()
        settings_name, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        dir_name = os.path.join(sublime.packages_path(), 'User')
        self.window.open_file(os.path.join(dir_name, settings_name + '.sublime-settings'))

    def is_enabled(self):
        return self.window.active_view() is not None
