## Porting Vula to OpenWrt

1. Install the build dependencies of the OpenWrt Build-System in https://openwrt.org/docs/guide-developer/toolchain/install-buildsystem and checkout the OpenWrt project from GitHub.


<code>$git clone https://github.com/openwrt/openwrt
$cd openwrt</code>


2. Update all base packets.

<code>$./scripts/feeds update -a
$./scripts/feeds install -a</code>

3. Select the target and sub target platform to which we want to
compile and save the choices to '.config'.

<code>$make menuconfig</code>

4. Download additional dependencies, in order to use all available cores while building the toolchain for the target platform.

<code>$make download
$make -j 'nproc'</code>

5. Create a new folder in the directory "package" and place the Makefile in it.

<code>$cd package
$mkdir vula
$cd vula
$touch Makefile</code>

6. Download the source code of Vula into the newly created package.

<code>$git clone https://codeberg.org/vula/vula</code>

7. Configure the Makefile.

A first version of the makefile can be found in the folder vula_openwrt. The interesting parts in the file are located in the 'Build/Compile' and the 'Package/vula/install' sections. In 'Build/Compile' we are calling the makefile of Vula with a target.

8. Go back to the openwrt root folder and run 

<code>$make menuconfig</code>

select the package 'vula' under the category 'network'. Save the chages to '.config', exit and run

<code>$make /package/vula/{clean,compile} V=sc</code>

The compiled package will be located under 'openwrt/bin/packages/target/base'

9. Add the Vula Module to LuCi

LuCI is located at /usr/lib/lua/luci/

To controller/vula/main.lua add

```
module("luci.controller.vula.main", package.seeall)
fuction index()
entry({"admin", "network", "vula"},
firstchild(), "vula", 20).dependent=false
entry({"admin", "network", "vula", "main"},
template("vula/main"), "vula", 20)
end
```

The first entry adds the module to the menu with the specified hierarchy.
The second entry adds the template in the second file as the main page of
this module.

To view/vula/main.htm add

```
<%+header%>
<h1><%Hello vula%></h1>
<%+footer%>
```

The header and footer parts are recommended to keep these elements
consistent throughout the whole UI.

## Further development

In the step 8., in 'Build/Compile' we are just calling the makefile of Vula with a target.
However, it might be necessary to 

- create a new phony in the Makefile of Vula 
- call `python3 setup.py` with some additional parameters
- adjust the setup.py file

The 'Package/vula/install' section is responsible for copying the built files
to the .ipk file.