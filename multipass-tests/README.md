**Note**: We plan to remove these multipass-based tests. See `podman/README.md`
for the new way to run a vula test network.

# Multipass test/dev environment

If you have `multipass` installed (a thing which lets you easily run Ubuntu VMs
on many modern GNU/Linux distros, or on Mac or Windows) then you can use the
scripts in this directory to setup virtual machines that communicate over
vula.

On GNU/Linux distros with `snapd` installed, you can install `multipass` by
running `sudo snap install multipass --classic`.

By default, these integration tests build a multipass image with vula
installed using a tool called `packer`. Run `apt install packer` to use this.

Alternately, you can maybe edit the config file in this directory to set
`IMAGE` to `20.10` instead of `packer`. This will be much slower as vula and
its dependencies must be installed on each instance instead of just once. This
functionality may be removed later, but remains for now so that we can test on
other multipass images without needing to make new packer configs for each. It
hasn't been tested recently.

## Quick start

Simply run `./start.sh` and three VMs will be created and will ping each other.

Aside from the multipass instances and the build (which happens in-place in
this source checkout) the host system will not be modified.

When you are finished and want to destroy the VMs, run `./stop.sh` and they
will be stopped and deleted.

## Development

Running `start.sh` will build an image with debs built from the current commit.
This does *not* include uncomitted changes.

You can run other scripts in this directory such as `retest.sh`, or you can run
`multipass shell vula-test1` to go exploring inside one of the VMs.

You can also run `./reinstall.sh` which will use `pip -e .` to install vula in
"editable" mode in each instance, so that that after you edit the code in your
local checkout of this repository (which is mounted in the VMs) you can simply
restart services (with `restart-services.sh`) without needing to run `setup.py
install` or anything else.

After having run `reinstall.sh`, using `./retest.sh` (which will remove all
non-key state and restart the services) should be sufficient to test code
changes most of the time (which is useful since starting the VMs from scratch
takes >2 minutes).

## Troubleshooting

If multipass gets confused, you can delete the instances and start over by
simply running `./stop.sh`. If you are unable to start new instances after
deleting the old ones (eg, because they are "being prepared" as happens
sometimes) you can fix this by restarting `multipassd` by running (assuming you
installed it via snap) `sudo snap restart multipass.multipassd`.

## Testing default route encryption in the multipass VMs

To enable the VMs to communicate with the host via vula, run `vula prefs add
iface_prefix_allowed mpqemubr` (if using the default qemu driver, or `virbr0`
if using the libvirt) and then stop vula (`systemctl stop vula.slice`) and then
start it again (`vula start`).

While the host is aware of the VM peers, some tests such as retest.sh and
test-repair.sh will not work because they take down the interface inside the VM
which renders it unreachable. This may or may not be fixed soon; for now, the
authors usually don't keep the multipass interface in the
`iface_prefix_allowed` allowed list on the host.
