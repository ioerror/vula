# Cross Compilation for the Android platform

This is a guide to help you cross compile the Python interpreter and some of its
required libraries in order to run it on an Android phone through ADB root. The
reason behind all of this is to, eventually, test-run some modules of Vula on
Android.

### Requirements
- An Android phone with the USB debugging and Rooted debugging options 
  activated.
- A computer with Python 3.8.12, ADB and the Android NDK installed.

*Please note that on some phone, rooted ADB access might require a  rooted phone.
Root access is necessary as the new binaries will have to be authorized to run
(`chmod +x`) and this can only be achived with it.*


### Compilation
Open `cross-compile.sh` in a text editor, correct the `NDK` variable for it to
point to where you installed the Android NDK. You can also edit the `TARGET`
variable to what your device need (Please note that only `aarch64-linux-android`
was tested). Save the changes, make sure your current directory is this one,
and run the script.

### Install and run the binaries on an Android phone
Plug your Android phone in the computer. From this folder, run:

```
adb root
adb remount
adb push ./prebuild /
adb shell
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/prebuild/lib
chmod +x /prebuild/bin/*
export PATH="/prebuild/bin/:$PATH"
python3 --version
```

If this first part went well, the ADB shell should have printed 
`Python 3.8.12`.
Now, `pip` and all pure python dependencies can be installed:

```
python3 -m ensurepip
python3 -m pip install wheel pydbus click zeroconf pyroute2 schema pyyaml \
packaging hkdf qrcode
```

### TODO

Python 3.8.12 seems to be running fine, but some required libraries of Vula
would still need to be cross compiled and packaged into wheel packages.

 - [ ] Gi (pyobject and pycairo)
 - [ ] PyNaCl
 - [ ] sibc
 - [ ] cryptography

The supported wheel tags are the following:

```
Compatible tags: 30
cp38-cp38-linux_aarch64
cp38-abi3-linux_aarch64
cp38-none-linux_aarch64
cp37-abi3-linux_aarch64
cp36-abi3-linux_aarch64
cp35-abi3-linux_aarch64
cp34-abi3-linux_aarch64
cp33-abi3-linux_aarch64
cp32-abi3-linux_aarch64
py38-none-linux_aarch64
py3-none-linux_aarch64
py37-none-linux_aarch64
py36-none-linux_aarch64
py35-none-linux_aarch64
py34-none-linux_aarch64
py33-none-linux_aarch64
py32-none-linux_aarch64
py31-none-linux_aarch64
py30-none-linux_aarch64
cp38-none-any
py38-none-any
py3-none-any
py37-none-any
py36-none-any
py35-none-any
py34-none-any
py33-none-any
py32-none-any
py31-none-any
py30-none-any
```
