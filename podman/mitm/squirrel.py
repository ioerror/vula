"""
Mallory's script to intercept vula traffic of unpinned peers.
 ___ _   _                                __  __       _ _                  _  # noqa: W605, E501
|_ _| |_( )___    __ _   _ __ ___   ___  |  \/  | __ _| | | ___  _ __ _   _| | # noqa: W605, E501
 | || __|// __|  / _` | | '_ ` _ \ / _ \ | |\/| |/ _` | | |/ _ \| '__| | | | | # noqa: W605, E501
 | || |_  \__ \ | (_| | | | | | | |  __/ | |  | | (_| | | | (_) | |  | |_| |_| # noqa: W605, E501
|___|\__| |___/  \__,_| |_| |_| |_|\___| |_|  |_|\__,_|_|_|\___/|_|   \__, (_) # noqa: W605, E501
                                                                      |___/    # noqa: W605
"""
import os
from scapy.all import sniff, wrpcap
from pyfiglet import Figlet
from printy import printy

# from subprocess import Popen, PIPE


def capture(file: str, timeout: int) -> None:
    """
    Try to use tcpdump directly before using this function here.
    Scapy is not intend/optimized for packet capturing
    """
    if os.path.exists(file):
        print("[+] Delete existing Capture file")
        os.unlink(file)

    print("[+] Start sniffing...")
    pkt = sniff(timeout=timeout)

    print("[+] Stop sniffing")
    wrpcap(file, pkt)

    # Variant with TCPdump
    # p = Popen(["tcpdump", "-w",file])
    # p.send_signal(subprocess.signal.SIGTERM)


def print_banner() -> None:
    f = Figlet()
    printy(f.renderText("It's a me Mallory!"), 'o>')


def main():
    print_banner()
    # file = "./podman/mitm/capture.pcap"
    # capture(file, timeout=30)
    print("[+] Done, Goodbye! ")


if __name__ == "__main__":
    main()
