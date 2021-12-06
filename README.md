## Prerequisites
```
sudo apt install gnome-tweaks
sudo apt install gnome-shell-extensions
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