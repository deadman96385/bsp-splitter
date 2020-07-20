# bsp-splitter

This is admittedly a pretty bad script that takes a bsp grabs the aosp commit history and then copies the original files back over and commits that to see roughly what was changed vs google aosp. I tried to get it all done via git but had issues, so had to resort to copying the files which means certain aosp repos are unsupported due to symlinking in the repo manifest. They are listed in the script.

You will need github's cli tool called hub and have it setup pre running this script aka run "hub create test" enter in your creds so it can pull an oauth token and then the script will do its bussiness.
