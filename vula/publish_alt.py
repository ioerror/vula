import csv
import fcntl
import hashlib
import json
import math
import random
import socket
import struct
import threading
import time
import zlib
from logging import Logger, getLogger
from queue import Empty, Queue
from typing import Optional

import click
import nacl.secret
import nacl.utils
import pydbus
from gi.repository import GLib

from .constants import (
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
    _PUBLISH_ALT_DBUS_NAME,
)


class Publish_Alt:

    dbus = '''
    <node>
      <interface name='local.vula.publishalt1.Control'>
        <method name='start'>
            <arg type='as' name='ip_addrs' direction='in'/>
        </method>
        <method name='stop'>
        </method>
      </interface>
    </node>
    '''

    def __init__(
        self,
        descriptor: str,
        verbose: bool,
        is_reply: bool,
        broadcast_mac: bytes,
        ethernet_type: bytes,
        hardware_type: bytes,
        protocol_type: bytes,
        hardware_size: bytes,
        protocol_size: bytes,
        zero_mac: bytes,
        interval_min: float,
        interval_max: float,
        op_code: bytes,
        arp_packet_max_length: int,
        formatting_string: str,
        hardware_address_ioctl_code: int,
        pa_address_code: int,
        time_interval: int,
    ):
        self.descriptor_cli = descriptor
        self.descriptor: dict = {}
        self.verbose = verbose
        self.is_reply = is_reply
        self.broadcast_mac = broadcast_mac
        self.ethernet_type = ethernet_type
        self.hardware_type = hardware_type
        self.protocol_type = protocol_type
        self.hardware_size = hardware_size
        self.protocol_size = protocol_size
        self.zero_mac = zero_mac
        self.interval_min = interval_min
        self.interval_max = interval_max
        self.op_code = op_code
        self.arp_packet_max_length = arp_packet_max_length
        self.formatting_string = formatting_string
        self.hardware_address_ioctl_code = hardware_address_ioctl_code
        self.pa_address_code = pa_address_code
        self.time_interval = time_interval
        self.log: Logger = getLogger()
        self.publish_entries: Queue = Queue()
        self.packets: Queue = Queue()
        self.active = False
        self.publishing_thread: threading.Thread
        self.packet_sending_thread: threading.Thread
        self.bus = pydbus.SystemBus()
        self.organize = self.bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
        self.ip_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def get_descriptors(self) -> None:
        """
        Update descriptors by querying organize
        """
        self.organize_descriptors = json.loads(
            self.organize.our_latest_descriptors()
        )

    def set_descriptors(self, sock: dict) -> None:
        """
        Set descriptor of ip
        """
        self.descriptor[sock["ip"]] = self.load_descriptor(sock["ip"])
        self.log.debug("Descriptors " + str(self.descriptor))

    def load_descriptor(self, ip: str) -> str:
        """
        Undo the JSON stuff done in organize and return descriptor
        """
        return " ".join(
            "%s=%s;" % kv
            for kv in sorted(self.organize_descriptors.get(ip).items())
        )

    def get_information(self, sock: dict) -> None:
        """
        Update specific information
        """
        sock["dest_ip"] = self.get_arp(sock)
        self.op_code = self.get_op_code()
        self.set_descriptors(sock)

    def run(self) -> None:
        """
        Main body for publishing thread
        """
        while self.active:
            self.get_descriptors()
            self.process_publish_entry(time.time())
            time.sleep(0.1)

    def process_publish_entry(self, t: float) -> bool:
        """
        Process queue of publishing entries. Go through FIFO
        queue and send descriptors. Reinsert into queue if periodic
        """
        try:
            publish_entry = self.publish_entries.get_nowait()
            if t - publish_entry["updated"] > self.time_interval:
                self.log.debug(publish_entry)
                # get dynamic information
                self.get_information(publish_entry)
                message = self.compress_and_encrypt(
                    self.descriptor[publish_entry["ip"]],
                    publish_entry["mac_addr"],
                )  # compress and encrypt message
                # generate packet header
                self.packets.put(
                    {
                        "packets": self.get_packets(publish_entry, message),
                        "socket": publish_entry["socket"],
                    }
                )
                publish_entry["updated"] = t
                if not publish_entry["periodic"]:
                    self.log.debug(
                        "dropping entry because it has been processed"
                    )
                else:
                    self.log.debug("adding entry back into queue")
                    self.publish_entries.put(publish_entry)
            else:
                self.publish_entries.put(publish_entry)
            return True
        except Empty:
            return False

    def get_packets(self, sock: dict, packet_payload: bytes) -> list:
        """
        Split message up into packets and return them for processing
        """
        self.log.debug("getting packets")
        packet_header = self.generate_header(sock)
        # segment encrypted payload into chunks of 18 bytes per packet
        # for a total packet length of 60 bytes
        packets = []
        number_of_packets = math.ceil(
            len(packet_payload)
            / (self.arp_packet_max_length - len(packet_header))
        )
        for i in range(number_of_packets):
            packet = (
                packet_header
                + packet_payload[
                    i
                    * ((self.arp_packet_max_length - len(packet_header))) : (
                        i + 1
                    )  # add corresponding packet chunk
                    * ((self.arp_packet_max_length - len(packet_header)))
                ]
            )
            packets.append(packet)
        return packets

    def send_packets(self) -> None:
        """
        Main body for sending thread. Sends packets in queue over the network.
        Wait for random duration of time between sending.
        """
        self.log.debug("setting up packet sending thread")
        while self.active:
            try:
                entry = self.packets.get_nowait()
                packets = entry["packets"]
                for i in range(len(packets)):
                    self.log.debug(f"Sending packet {i + 1} of {len(packets)}")
                    entry["socket"].send(packets[i])
                    time.sleep(
                        random.uniform(self.interval_min, self.interval_max)
                    )
            except Empty:
                pass
            time.sleep(0.5)

    def get_op_code(self) -> bytes:
        """
        Get operation code.
        """
        # set op code, 0x01 for request and 0x02 for reply
        self.log.debug(
            "Sending packet as reply."
            if self.is_reply
            else "Sending packet as request."
        )
        if self.is_reply:
            return b"\x00\x02"
        else:
            return b"\x00\x01"

    def get_ip(self, interface: str) -> str:
        """
        Get IP address of interface
        """
        return socket.inet_ntoa(
            fcntl.ioctl(
                self.ip_socket.fileno(),
                self.pa_address_code,
                struct.pack(
                    self.formatting_string,
                    interface[:15].encode("utf-8"),
                ),
            )[20:24]
        )

    def get_interface_name(self, ip: str) -> Optional[str]:
        """
        Return interface name associated withip
        """
        interfaces = socket.if_nameindex()
        for interface in interfaces:
            try:
                if ip == self.get_ip(interface[1]):
                    return interface[1]
            except OSError:
                pass
        return None

    def get_mac(self, sock: dict) -> bytes:
        """
        Get mac address of interface
        """
        return fcntl.ioctl(
            sock["socket"].fileno(),
            self.hardware_address_ioctl_code,
            struct.pack(
                self.formatting_string, bytes(sock["if_name"][:15], "utf-8")
            ),
        )[18:24]

    def compress_and_encrypt(self, msg: str, encryption_key: bytes) -> bytes:
        """
        Encrypt given message with key. Add timestamp for obfuscation
        """
        message = (
            str(int(time.time())) + msg
        )  # add unix timestamp to add some randomness to encrypted text
        hd = bytes(message, "utf-8")  # encode message into bytes
        hdc = zlib.compress(hd)  # compress with zlib
        key = hashlib.sha256(
            encryption_key
        ).digest()  # generate key from source mac
        box = nacl.secret.SecretBox(key)  # generate enryptor
        nonce = nacl.utils.random(
            nacl.secret.SecretBox.NONCE_SIZE
        )  # add default nonce
        self.log.debug("message length before compression: " + str(len(hd)))
        self.log.debug("message length after compression: " + str(len(hdc)))
        return box.encrypt(hdc, nonce)  # return encryped text

    def generate_header(self, sock: dict) -> bytes:
        """
        Assemble ARP header
        """
        packet_header = self.broadcast_mac
        packet_header += sock["mac_addr"]
        packet_header += self.ethernet_type
        packet_header += self.hardware_type
        packet_header += self.protocol_type
        packet_header += self.hardware_size
        packet_header += self.protocol_size
        packet_header += self.op_code
        packet_header += sock["mac_addr"]
        packet_header += socket.inet_aton(sock["ip"])
        packet_header += self.zero_mac
        packet_header += sock["dest_ip"]
        return packet_header

    def get_arp(self, sock: dict) -> bytes:
        """
        Pick random entry of ARP cache to be used as destination address.
        """
        with open("/proc/net/arp") as arp_table:  # read arp cache
            reader = list(
                csv.reader(arp_table, skipinitialspace=True, delimiter=" ")
            )
        dest_ip = b""
        arp_cache = [
            a[0] for a in reader[1:]
        ]  # skip header line and read ip field
        if len(arp_cache) == 0:
            dest_ip = (
                socket.inet_aton(self.get_ip(sock["if_name"]))[0:3] + b"\x01"
            )  # if chache is empty, take 0x01 address of own ip
        else:
            random_ip = random.choice(arp_cache)  # pick random ip
            dest_ip = socket.inet_aton(random_ip)
            self.log.debug("Setting random arp ip as destination.")
            self.log.debug("Arp cache: " + str(arp_cache))
            self.log.debug("Chosen Destination ip: " + str(random_ip))
        return dest_ip

    def start(self, ip_addrs: list[str]) -> None:
        """
        DBus exposed controlling function. Takes list of IPs and
        starts publishing process
        """
        self.log.info("Starting alternative publish")
        self.setup(ip_addrs)
        if not self.active:
            self.active = True
            self.packet_sending_thread = threading.Thread(
                target=self.send_packets
            )
            self.packet_sending_thread.start()
            self.publishing_thread = threading.Thread(target=self.run)
            self.publishing_thread.start()

    def stop(self) -> None:
        """
        DBus exposed controlling function. Stops discovering process
        """
        self.log.info("Stoping alternative publish")
        self.active = False
        self.clear_broadcast_queue()

    def setup(self, ip_addrs: list[str], periodically: bool = True) -> None:
        """
        Processes list of IP adresses and adds entries to be processed
        """
        self.log.debug("publish setup")
        for ip in ip_addrs:
            s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
            if_name = self.get_interface_name(ip)
            s.bind((if_name, 0))
            socket_entry = {
                "socket": s,
                "periodic": periodically,
                "if_name": if_name,
                "ip": ip,
                "updated": 0,
            }
            socket_entry["mac_addr"] = self.get_mac(socket_entry)
            self.publish_entries.put(socket_entry)

    def clear_broadcast_queue(self) -> None:
        """
        Clears out all entries and closes the associated sockets
        """
        while not self.publish_entries.empty():
            socket_entry = self.publish_entries.get()
            socket_entry["socket"].close()
            del socket_entry["socket"]
        self.publish_entries = Queue()

    @classmethod
    def daemon(
        cls,
        descriptor,
        verbose,
        is_reply,
        broadcast_mac,
        ethernet_type,
        hardware_type,
        protocol_type,
        hardware_size,
        protocol_size,
        zero_mac,
        interval_min,
        interval_max,
        op_code,
        arp_packet_max_length,
        formatting_string,
        hardware_address_ioctl_code,
        pa_address_code,
        time_interval,
    ) -> None:
        """
        Sets up dbus
        """
        loop = GLib.MainLoop()

        publish = cls(
            descriptor,
            verbose,
            is_reply,
            broadcast_mac,
            ethernet_type,
            hardware_type,
            protocol_type,
            hardware_size,
            protocol_size,
            zero_mac,
            interval_min,
            interval_max,
            op_code,
            arp_packet_max_length,
            formatting_string,
            hardware_address_ioctl_code,
            pa_address_code,
            time_interval,
        )

        publish.log.info("dbus enabled")
        system_bus = pydbus.SystemBus()
        system_bus.publish(_PUBLISH_ALT_DBUS_NAME, publish)

        loop.run()


@click.command(short_help="Layer 2 alternate publish daemon")
@click.option(
    "--descriptor",
    required=False,
    type=str,
    help="descriptor to use for sending packets.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="show additional information.",
)
@click.option(
    "--is_reply",
    is_flag=True,
    default=False,
    help="Send reply packets instead of request.",
)
@click.option(
    "--broadcast_mac",
    default=b"\xff\xff\xff\xff\xff\xff",
    type=bytes,
    help="Broadcast mac address",
)
@click.option(
    "--ethernet_type",
    default=b"\x08\x06",
    type=bytes,
    help="Ethernet Type",
)
@click.option(
    "--hardware_type",
    default=b"\x00\x01",
    type=bytes,
    help="Hardware Type",
)
@click.option(
    "--protocol_type",
    default=b"\x08\x00",
    type=bytes,
    help="Protocol Type",
)
@click.option(
    "--hardware_size", default=b"\x06", type=bytes, help="Hardware Size"
)
@click.option(
    "--protocol_size", default=b"\x04", type=bytes, help="Protocol Size"
)
@click.option(
    "--zero_mac",
    default=b"\x00\x00\x00\x00\x00\x00",
    type=bytes,
    help="Empty mac address",
)
@click.option(
    "--interval_min",
    default=0.01,
    type=float,
    help="Minimum value of packet delay",
)
@click.option(
    "--interval_max",
    default=0.1,
    type=float,
    help="Maximum value of packet delay",
)
@click.option("--op_code", default=None, type=float, help="Operation Code")
@click.option(
    "--arp_packet_max_length",
    default=60,
    type=int,
    help="Max packet length",
)
@click.option(
    "--formatting_string",
    default="256s",
    type=str,
    help="Formatting string",
)
@click.option(
    "--hardware_address_ioctl_code",
    default=0x8927,
    type=int,
    help="IOCTL code to get hw address",
)
@click.option(
    "--pa_address_code",
    default=0x8915,
    type=int,
    help="IOCTL code to get PA address",
)
@click.option(
    "--time_interval", default=90, type=int, help="Time in between packets"
)
def main(
    descriptor,
    verbose,
    is_reply,
    broadcast_mac,
    ethernet_type,
    hardware_type,
    protocol_type,
    hardware_size,
    protocol_size,
    zero_mac,
    interval_min,
    interval_max,
    op_code,
    arp_packet_max_length,
    formatting_string,
    hardware_address_ioctl_code,
    pa_address_code,
    time_interval,
):
    arp_daemon = Publish_Alt.daemon(
        descriptor,
        verbose,
        is_reply,
        broadcast_mac,
        ethernet_type,
        hardware_type,
        protocol_type,
        hardware_size,
        protocol_size,
        zero_mac,
        interval_min,
        interval_max,
        op_code,
        arp_packet_max_length,
        formatting_string,
        hardware_address_ioctl_code,
        pa_address_code,
        time_interval,
    )
    arp_daemon.log.debug("main")


if __name__ == "__main__":
    main()
