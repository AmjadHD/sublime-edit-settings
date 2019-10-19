# sublime-edit-settings

A patch for the sublime text edit_settings command

![in_action](https://user-images.githubusercontent.com/33235928/67150807-86bfc900-f2bc-11e9-96a3-5de3b0ed15b8.gif)

![image](https://user-images.githubusercontent.com/33235928/67150882-c89d3f00-f2bd-11e9-8853-4a7df0b8cc5a.png)

![image](https://user-images.githubusercontent.com/33235928/67150861-7825e180-f2bd-11e9-81f8-81f32e46631b.png)

## Usage

#### without arguments
- displays a list of kinds of configuration files,
choosing one displays a list of files of the chosen kind.

#### with `base_file`
- opens the file as usual (`kind` is ignored)

#### with `kind` only
- displays a list of files of the kind `kind`

## Note
- files in the `User` folder are ignored from lists
- for files specifying platfom, only those specific to the current platform are included
