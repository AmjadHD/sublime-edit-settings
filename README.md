# sublime-edit-settings
a patch for the sublime text edit_settings command

## Usage

**without arguments**
- displays a list of types of preferences files
choosing one displays a list of files of the chosen type.
**with `base_file` only**
- opens the file as usual
**with `type` only**
- displays a list of files of the type `type`
**with `base_file` and `type`**
- opens the file as usual (`type` is ignored)

## Note
- files in the `User` folder are ignored from lists
- for files specifying platfom, only those specific to the current platform are included
