#!/bin/bash

bsp_path='/media/iscle/AndroidSources/alps_q/V9.107/t-alps-q0.mp1-V9.107'
manifest='android-10.0.0_r2'
branch_name='t-alps-q0.mp1-V9.107'
temp_dir_path='/media/iscle/AndroidSources/temp'

# The following repos need to be done manually due to symlinks
# build/make
# build/soong
# hardware/qcom/sdm845/data/ipacfg-mgr
# sdk

# Get the current directory for later
cur_dir=$(pwd)

# Delete any previous temp folder
rm -rf $temp_dir_path
# Delete any previous files
rm -f not_found.txt
rm -f no_changes.txt

# Known repo detection
while read -r line; do
    if [ -d "${bsp_path}/${line}/" ]; then
        #echo ${bsp_path}/${line}/
        mkdir $temp_dir_path
        cd ${temp_dir_path}/
        git init
        git remote add google https://android.googlesource.com/platform/$line
        git fetch google
        git checkout tags/${manifest} -b $branch_name
        cp -rf ${bsp_path}/${line}/* .

        if [[ -z $(git status -s) ]]; then
            echo /${line}/ has no changes!
            echo $line >> ${cur_dir}/no_changes.txt
        else
            git add --all
            git commit -m "Add MediaTek changes
Branch: ${branch_name}"
            hub create mtk-watch/android_$(echo "${line}" | sed 's#/#_#g')
            git push -f origin $branch_name
        fi

        rm -rf $temp_dir_path
    else
        echo Warning: /${line}/ not found!
        echo $line >> ${cur_dir}/not_found.txt
    fi
done < repos.txt

# Cleanup
rm -rf $temp_dir_path
