# sublime-edit-settings
a patch for the sublime text edit_settings command

![screenshot_1](https://user-images.githubusercontent.com/33235928/47184421-e7739900-d32a-11e8-9769-25a3d5933004.png)

![screenshot_2](https://user-images.githubusercontent.com/33235928/47184717-b34ca800-d32b-11e8-91be-7059a7a90b23.png)

## Usage

#### without arguments
- displays a list of types of preferences files
choosing one displays a list of files of the chosen type.
#### with `base_file` only
- opens the file as usual
#### with `type` only
- displays a list of files of the type `type`
#### with `base_file` and `type`
- opens the file as usual (`type` is ignored)

## Note
- files in the `User` folder are ignored from lists
- for files specifying platfom, only those specific to the current platform are included
