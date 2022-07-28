include $(TOPDIR)/rules.mk

PKG_NAME:=Vula
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

include $(INCLUDE_DIR)/package.mk

define Package/vula
	SECTION:=utils
	CATEGORY:=Network
	TITLE:=Vula
	URL:=https://codeberg.org/vula/vula
endef

define Package/vula/description
	Automatic local network encryption
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) ./vula/* $(PKG_BUILD_DIR)/
endef

define Build/Compile
	# Here we can call the Makefile from Vula
	$(MAKE) pypi-build -C $(PKG_BUILD_DIR)
endef

define Package/vula/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/vula $(1)/usr/bin/
endef

$(eval $(call BuildPackage,vula))
