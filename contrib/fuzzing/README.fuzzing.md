## Fuzzer

This fuzzer is using the atheris python fuzzer from youtube.
Its main functions are in the atheris python module.

With this fuzzer it is possible to fuzz any function that you specify; like in the simple example below:

    import atheris
    import sys

    def TestOneInput(data):
        if data == b"bad":
            raise RuntimeError("Badness!")

    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

If a potential exception is thrown, the fuzzer remembers the input.
At the end the fuzzer creates a crash file containing the inputs that caused an error.
The vulaFuzzer.py fuzzes the "vula verify against [NAME]" for faulty inputs.

For more information you can refer to atheris github: https://github.com/google/atheris

### Vula Inputs
The possible Inputs with the commandline can be represented like this:
* vula
  * start
  * repair
  * rediscover
  * release-gateway
  * configure
  * discover
  * publish
  * organize
  * verify [options]
    * my-vk
    * my-descriptor
    * against NAME
    * scan NAME
  * status
  * peer
  * prefs
  
##### Known Exceptions:

|Command|Exception|Cause|
|------|---------|-----|
|vula discover|GDBus.Error:org.freedesktop.DBus.Error.AccessDenied: Connection ":1.173" is not allowed to own the service "local.vula.discover" due to security policies in the configuration file (9)|The user making the command was not in the sudo group.|
|vula discover|RuntimeError: name already exists on the bus|Unknown, probably when directly run as user root|
|vula publish|GDBus.Error:org.freedesktop.DBus.Error.AccessDenied: Connection ":1.174" is not allowed to own the service "local.vula.discover" due to security policies in the configuration file (9)|The user making the command was not in the sudo group.|
|vula organize|PermissionError: [Errno 13] Permission denied: '/var/lib/vula-organize/keys.yaml' -> '/var/lib/vula-organize/keys.yaml.1644055287.17229'|Unknown, but probably caused when the user making the command is not in the sudo group.|
|vula verify scan [NAME]|Attribute Error: 'NoneType' object has no attribute 'VideoCapture'|Unknown|

Potential place for exceptions:
* vula verify scan [NAME]
* vula verify against [NAME]

##### Current results
At the moment the fuzzer only checks the "vula verify against [NAME]" command for any exceptions.
This did not result in any found crashes as of yet.

The next steps to take would be to expand the scope as well as the complexity of the fuzzer.
This would then make it possible to check a broader part of vula.
