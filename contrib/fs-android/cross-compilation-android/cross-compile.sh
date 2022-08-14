#!/bin/bash
export NDK=/opt/android-ndk
export PREFIX=$PWD/prebuild
#export CPPFLAGS="-fPIC -shared"
export TOOLCHAIN=$NDK/toolchains/llvm/prebuilt/linux-x86_64
export TARGET=aarch64-linux-android
export API=30
export AR=$TOOLCHAIN/bin/llvm-ar
export CC=$TOOLCHAIN/bin/$TARGET$API-clang
export AS=$CC
export CXX=$TOOLCHAIN/bin/$TARGET$API-clang++
export LD=$TOOLCHAIN/bin/ld
export RANLIB=$TOOLCHAIN/bin/llvm-ranlib
export STRIP=$TOOLCHAIN/bin/llvm-strip
export READELF=$TOOLCHAIN/bin/llvm-readelf
export LLVM_PROFDATA=$TOOLCHAIN/bin/llvm-profdata

if [ -d "$PREFIX" ]; then
	rm -Rf $PREFIX/*
else
	mkdir $PREFIX
fi

# Clean or download zlib dependency
if [ -d "zlib-1.2.11" ]; then
	cd zlib-1.2.11/
	make clean
	cd ..
else
	# Downloading the library
	wget https://www.zlib.net/fossils/zlib-1.2.11.tar.gz
	tar -xvf zlib-1.2.11.tar.gz
	rm zlib-1.2.11.tar.gz
	# Creating the configuration script specific to this library
	echo "#!/bin/bash
./configure --prefix \$PREFIX --enable-shared
make
make install" > zlib-1.2.11/cross-compile.sh
	chmod +x zlib-1.2.11/cross-compile.sh
fi


# Clean or download openssl dependency
if [ -d "openssl-3.0.0" ]; then
	cd openssl-3.0.0/
	make clean
	cd ..
else
	# Downloading the library
	wget https://www.openssl.org/source/old/3.0/openssl-3.0.0.tar.gz 
	tar -xvf openssl-3.0.0.tar.gz
	rm openssl-3.0.0.tar.gz
	# Creating the configuration script specific to this library
	echo "#!/bin/bash
export ANDROID_NDK_ROOT=\$NDK
PATH=\$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin:\$ANDROID_NDK_ROOT/toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin:\$PATH
./Configure android-arm64 -D__ANDROID_API__=\$API --prefix=\$PREFIX --openssldir=\$PREFIX \
		ac_cv_buggy_getaddrinfo=no \
                ac_cv_file__dev_ptmx=no \
		ac_cv_file__dev_ptc=no \
		ac_cv_have_long_long_format=yes
make
make install" > openssl-3.0.0/cross-compile.sh
	chmod +x openssl-3.0.0/cross-compile.sh
fi

# Clean or download libffi dependency
if [ -d "libffi-3.4.2" ]; then
	cd libffi-3.4.2/
	make clean
	cd ..
else
	# Downloading the library
	wget https://github.com/libffi/libffi/releases/download/v3.4.2/libffi-3.4.2.tar.gz
	tar -xvf libffi-3.4.2.tar.gz
	rm libffi-3.4.2.tar.gz
	# Creating the configuration script specific to this library
	echo "#!/bin/bash
./configure --prefix \$PREFIX --host \$TARGET --build x86_64-pc-linux-gnu --enable-shared \
		ac_cv_buggy_getaddrinfo=no \
                ac_cv_file__dev_ptmx=no \
		ac_cv_file__dev_ptc=no \
		ac_cv_have_long_long_format=yes
make
make install" > libffi-3.4.2/cross-compile.sh
	chmod +x libffi-3.4.2/cross-compile.sh
fi

# Clean or download libuuid dependency
if [ -d "libuuid-1.0.3" ]; then
	cd libuuid-1.0.3/
	make clean
	cd ..
else
	# Downloading the library
	wget https://sourceforge.net/projects/libuuid/files/libuuid-1.0.3.tar.gz
	tar -xvf libuuid-1.0.3.tar.gz
	rm libuuid-1.0.3.tar.gz
	# Creating the configuration script specific to this library
	echo "#!/bin/bash
./configure --prefix \$PREFIX --host \$TARGET --build x86_64-pc-linux-gnu --enable-shared --with-pic \
		ac_cv_buggy_getaddrinfo=no \
                ac_cv_file__dev_ptmx=no \
		ac_cv_file__dev_ptc=no \
		ac_cv_have_long_long_format=yes
autoreconf -i -f
make
make install" > libuuid-1.0.3/cross-compile.sh
	chmod +x libuuid-1.0.3/cross-compile.sh
fi


# Clean or download ncurses dependency
if [ -d "ncurses-6.3" ]; then
	cd ncurses-6.3/
	make clean
	cd ..
else
	# Downloading the library
	wget https://invisible-mirror.net/archives/ncurses/ncurses-6.3.tar.gz
	tar -xvf ncurses-6.3.tar.gz
	rm ncurses-6.3.tar.gz
	# Creating the configuration script specific to this library
	echo "#!/bin/bash
./configure --prefix \$PREFIX --host=\$TARGET --build x86_64-pc-linux-gnu --enable-shared --with-pic --with-shared \
		ac_cv_buggy_getaddrinfo=no \
                ac_cv_file__dev_ptmx=no \
		ac_cv_file__dev_ptc=no \
		ac_cv_have_long_long_format=yes
make
make install
/bin/cp -rf ./lib/* \$PREFIX/lib/
/bin/cp -rf ./include/panel.h \$PREFIX/include/ncurses/panel.h
/bin/cp -rf ./include/menu.h \$PREFIX/include/ncurses/menu.h
/bin/cp -rf ./include/form.h \$PREFIX/include/ncurses/form.h" > ncurses-6.3/cross-compile.sh
	chmod +x ncurses-6.3/cross-compile.sh
fi

# Clean or download the Python interpreter
if [ -d "Python-3.8.12" ]; then
	cd Python-3.8.12/
	make clean
	cd ..
else
	# Downloading the library
	wget https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz
	tar -xvf Python-3.8.12.tgz
	rm Python-3.8.12.tgz
	# Creating the configuration script specific to this library
	echo "#!/bin/bash
export CPPFLAGS=\"-fPIC -I\$PREFIX/include/ -I\$PREFIX/include/ncurses\"
export CC=\"\$TOOLCHAIN/bin/\$TARGET\$API-clang -fPIC\"
export CXX=\"\$TOOLCHAIN/bin/\$TARGET\$API-clang++ -fPIC\"
export LDFLAGS=\"-L\$PREFIX/lib/\"
#export LIBS=\"-lncurses\"
#export BLDSHARED=\"\$CC -shared\"

./configure --host \$TARGET --build x86_64-pc-linux-gnu --disable-ipv6 \
		--with-openssl=\$PREFIX \
		ac_cv_buggy_getaddrinfo=no \
                ac_cv_file__dev_ptmx=no \
		ac_cv_file__dev_ptc=no \
		ac_cv_have_long_long_format=yes \
		--prefix=\$PREFIX \
		--exec-prefix=\$PREFIX \
		--enable-shared
make
make install" > Python-3.8.12/cross-compile.sh
	chmod +x Python-3.8.12/cross-compile.sh
fi

# Cross-compile

cd zlib-1.2.11/
./cross-compile.sh
cd ..

cd openssl-3.0.0/
./cross-compile.sh
cd ..

cd libffi-3.4.2/
./cross-compile.sh
cd ..

cd libuuid-1.0.3/
./cross-compile.sh
cd ..

cd ncurses-6.3/
./cross-compile.sh
cd ..

cd Python-3.8.12/
./cross-compile.sh
