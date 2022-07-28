# Current State of Vula on macOS

January 2022 by Isak Combrinck

[1. Installation](#installation)  
[2. Tests](#tests)  
[3. Debugging](#debugging)  
[4. Conclusion](#conclusion)

This is an overview of the current state of Vula on macOS. Its intention is to highlight the areas that still need work in order to get Vula work on macOS. This should serve as a guide for future developers, letting them know what has been done and where to continue.

I have approached the issue of porting Vula to macOS by assuming that it will work on macOS like it does on Linux. Going through the normal build, install and run workflow; noting where I encounter errors and how to overcome these.

<a name="installation">

## 1. Installation

You can install Vula on macOS without any errors or warnings as long as you install the pre-requisites and have the dbus error fix present in your version. This is helpful because it allows you to run Vula commands and see what they actually do on macOS, or in the current state, what error they give you.

### Pre-requisites

Install needed packages through brew and pip, these might already be present on your system.

```
brew install dbus pygobject3
```

```
pip install dbus-python cryptography packaging schema hkdf sibc pyhacl pyroute2
```

### Build

You can build Vula on macOS with no errors.

### Install

You can install Vula on macOS if the fix below is present in your version.

#### dbus error

When you run `sudo python3 setup.py install` it stops at `error: could not create '/usr/share/dbus-1': Operation not permitted`.

On macOS you are not allowed to write in the `/usr` directory as it is protected by System Integrity Protection.

FIX: This is fixed by changing the install path for macOS in setup.py.

STATUS: The fix is currently unmerged.

<a name="tests">

## 2. Tests

My second step has been to run the unit tests and see what they do on macOS. All tests should pass before continuing to the third step. Currently the tests complete with: 8 failed, 89 passed, 1 warning.

### Failed Tests

The following tests currently fail on macOS.

```
FAILED vula/sys_pyroute2.py::vula.sys_pyroute2.Sys.get_stats
FAILED vula/wg.py::vula.wg.\_wg_interface_list
FAILED test/test_peer.py::test.test_peer.TestDescriptor_qrcode
FAILED test/test_sys_pyroute2.py::TestSys::test_start_stop_monitor - OSError:...
FAILED test/test_sys_pyroute2.py::TestSys::test_monitor_newneigh - OSError: [...
FAILED test/test_sys_pyroute2.py::TestSys::test_monitor_netlink_msg - OSError...
FAILED test/test_sys_pyroute2.py::TestSys::test_monitor_bug - OSError: [Errno...
FAILED test/test_verify.py::TestVerifyCommands::test_my_vk - AttributeError: ...
```

### Warnings

Currently the only warning produced on macOS is a deprecation warning. This should not hinder Vula from being able to run on macOS and is to be addressed within the general scope of Vula development.

<a name="debugging">

## 3. Debugging

Once all tests pass, Vula should be ran and the output observed. It doesn't make sense to do this before the tests pass, as you are likely to see errors related to the tests that don't pass.

### Example

Just for the sake of experimentation, I have tried running Vula without fixing the tests that don't pass. This serves as an example for future developers, to see how I have gone about the process of debugging the output.

#### Normal Mode

This doesn't work and produces errors when trying most of the subcommands. For example:

```
vula status
```

returns with
`so far, the status command only works on linux`. This is to be expected and should only be further investigated once all tests pass.

#### Monolythic Mode

When you run:

```
sudo vula organize run --monolithic
```

Vula tries to generate the keys and write them to `/var/lib/vula-organize`. However, this folder doesn't exist on macOS and the system doesn't allow Vula to create it.

FIX: This can be fixed by manually creating the folder:

```
sudo mkdir /var/lib/vula-organize
```

This fix brings you one step further and the next output only contains the next error to be fixed. As mentioned above, this is expected and should only be further investigated once all tests pass.

<a name="conclusion">

## 4. Conclusion

By following the instructions I have provided you should be able to build, install and run (although not successfully) Vula on macOS. This should bring you to a state where it's easier to debug Vula and know what's still missing for it to function properly.

### Next Steps

The next step would be to fix the tests that don't pass.
Once this is done the different Vula commands can be ran and debugged/fixed as necessary.

### Considerations

While investigating Vula's compatibility with macOS a fellow student started implementing Vula in Go. This led me to re-think the idea of a macOS port. If Vula can be successfully implemented in another language that allows it to run cross-platform without any major code changes then a port might be unnecessary. This has to be considered when porting Vula to macOS. In the long run it might be less work to re-implement Vula once and not have to worry about platform specific code, especially if Windows, Android and iOS are to be supported.

However, this would only make sense if a large incompatibility is found that requires a lot of work to fix. So far all of the fixes have been minor and can be automated with the installation or fixed in the codebase with minimal effort.
