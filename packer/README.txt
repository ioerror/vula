This is a packer configuration Based on
https://discourse.ubuntu.com/t/building-multipass-images-with-packer/12361 and
https://learn.hashicorp.com/tutorials/packer/getting-started-build-image?in=packer/getting-started

To build it:
    packer build template.json

To launch the image:
    multipass launch file://$PWD/output-qemu/packer-qemu --disk 5G -n foo1
