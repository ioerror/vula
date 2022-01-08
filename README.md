## Prerequisites
```
sudo apt install gnome-tweaks
sudo apt install gnome-shell-extensions
```

## install

```
download project from git
sudo mv vula@bfh.ch /usr/share/gnome-shell/extensions
refresh gnome with "ALT+F2" and command "r"
```

## uninstall

```
go to /usr/share/gnome-shell/extensions
sudo rm -r vula@bfh
refresh gnome with "ALT+F2" and command "r"
```

## Debugging

#### Accessing the logs
```
journalctl /usr/bin/gnome-shell -f -o cat
```
or
```
journalctl /usr/bin/gnome-session -f -o cat
```

## Useful links
https://www.codeproject.com/Articles/5271677/How-to-Create-A-GNOME-Extension
https://wiki.gnome.org/Projects/GnomeShell/Extensions/EcoDoc/Applet
