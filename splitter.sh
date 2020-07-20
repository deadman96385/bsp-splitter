bsp_path='/speedy/t-alps-release-q0.mp1-V9.77'
manifest="android-10.0.0_r2"
branch_name="mtk_v9.77_10.0"
temp_dir_path='/speedy/testing/temp'

# The following repos need to be done manually due to symlinks
# build/make
# build/soong
# hardware/qcom/sdm845/data/ipacfg-mgr
# sdk

# Known repo detection
cat repos.txt | while read -r line;
do
if [ ! -d "${bsp_path}/${line}/" ] 
    then
	    echo /${line}/ not found
    else
	    #echo ${bsp_path}/${line}/
	    cd ${bsp_path}/${line}/
		cp -rf * ${temp_dir_path}
        git init
		git checkout -b temp
        git add --all
        git commit -a -m "BSP Changes"
		git remote add google https://android.googlesource.com/platform/$line
		git fetch --all
		git checkout tags/android-10.0.0_r2 -b $branch_name
		cp -rf ${temp_dir_path}/* .
		git add --all
		git commit -a -m "MTK Changes"
		hub create mtk-watch/android_$(echo "${line}"|sed 's#/#_#g')
		git push -f origin $branch_name
		rm -rf ${temp_dir_path}/*
    fi
done
