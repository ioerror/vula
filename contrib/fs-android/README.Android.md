# Portability Study for Vula on Android

The purpose of this document is to hopefully help anybody to gain
basic knowledge about the dilemmas that porting Vula to Android 
presents.

## Dependencies and Permissions analysis

To understand how Vula is organised check out
[DEPENDENCY.md](../../DEPENDENCY.md), which illustrates graphically
the structure and dependencies relationships of Vula.

To know exactly which library files and system calls Vula uses, see the
file [strace-vula.txt](strace-vula.txt). It was generated with the
command `strace sudo vula organize run --monolithic --no-dbus` as
Android does not have any D-Bus integrated.
During the test, it communicated with a peer and rediscovered the
network.

A list of all individual system calls Vula used when ran through
`strace` can be found in [raw-call-list.txt](raw-call-list.txt). 

Finally, a selection of a few pertinent lines were extracted from the
raw `strace-vula.txt` file into
[vula-dependencies.txt](vula-dependencies.txt). Listing principally 
system shared libraries and files that were accessed during its
execution.

## Strategies

Here are listed the two main strategies that have been taken in
considerations.

### Port the Vula reference implementation

This strategy has not been explored to its end due to lack of time. 
Nevertheless, some assumptions and facts can be drawn
from the current results. As of now, some Python libraries and
their C/C++ dependencies would still need to be cross compiled and
packaged in wheel files. Are all those libraries compatible with the
Android platform? Technically it seems to be the case, but the only way
to really know is through practical testing. Please see 
[cross-compilation-android](cross-compilation-android/) for 
more informations about this study.

If we now assume that the Python environment was functional and all the
Vula dependencies were installed, some parts of the python codebase
would obviously be incompatible with the platform (e.g. pydbus dependent
modules). Some other functionalities would need to be entirely
reimplemented (e.g. 
[Android VPN interface](https://developer.android.com/guide/topics/connectivity/vpn)
). These issues are already very demanding, not only for filtering out
which modules could potentially be used, but also because some modules
have dependencies they do not necessarily require. Thus, a
restructuration of the entire project would be necessary in order to 
achieve a satisfying result. Still, even after all that work, all that
can be guaranteed is that all the compatible modules could be tested,
and not that they would be functional.

With all of that in mind, even if the idea of using the original
codebase is quite charming and convenient for maintainability reasons,
the amount of work and the uncertainty to have any actually usable
results still outweigh the benefits. That is why we would not recommend
choosing this strategy for a port.

### Reimplementation

#### Native Android reimplementation

Given the above difficulties, we believe that the most suitable solution
would be to reimplement Vula in a dedicated version for Android, ideally
native (Java, Kotlin, or C++ via NDK). The freedom to rely on the APIs
provided by Android (SDK, NDK) will allow much better implementations
given the low complexity of Vula. Reimplementing Vula would be more
suitable as is, rather than to adapt it by adding a lot of haphazard
complexity that would not add any value to it.

#### Golang reimplementation (more modularity)

An implementation using Golang is also possible (like tailscale does for
its Android version,
[see tailscale's github](https://github.com/tailscale/tailscale-android)) 
however, the current version of Vula in Golang will not work right out of
the box on Android. It would be necessary to make substantial
modifications to the current Golang project.

#### Specifications (interoperability)

With either reimplementation strategies be it native or with Golang, a
clarification/specification is needed to guarantee interoperability
between the different Vula implementations (the reference one and the
Android version at least). Without a specification, the task of
achieving interoperability becomes exponentially harder.


## Adaptation

In order to port Vula for Android, we need a way to communicate with
the underlying service. For two of the listed strategies (Python
reference implementation, Golang reimplementation), an IPC would have
to be developed. Three interesting solutions caught our attention:
-   IPC using standard input and output
-   IPC using socket
-   JNI (Java native interface)

Among these solutions, the JNI option is probably the best, because 
there is no message protocol to develop just C/C++ functions that would
be mapped to native methods (see the following snippet).

*Java code*

```
class TestJNI1 {
  public native void great(String name);
  static {
    System.loadLibrary("mylib");
  }
  // ...
}
```

*`mylib` shared library implementation*.

```
#include <jni.h>
JNIEXPORT void JNICALL Java_TestJNI1_great(JNIEnv* env, jstring name) {
    // content here
}
```

## Conclusion

After exploring the different options at hand, we had to decide which
one we would recommend to anyone attempting to implement Vula on
Android. Considering the different strengths and disadvantages of each
strategy outlined before, we recommend going for the native Android
reimplementation. Especially since the Python reference implementation 
is more complex, it quickly becomes clear that the native implementation
is a wiser choice as well as more efficient.
