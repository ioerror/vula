import hashlib
import socket
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
    _DISCOVER_ALT_DBUS_NAME,
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
)

# assuming 60 byte packets. we have 18 bytes padding/payload.
PAYLOAD_MAX_SIZE = 18


class Discover_Alt:

    dbus = '''
    <node>
      <interface name='local.vula.discoveralt1.Control'>
        <method name='start'>
        </method>
        <method name='stop'>
        </method>
      </interface>
    </node>
    '''

    def __init__(
        self,
        insert_into_vula: bool,
        max_age: int,
        arp_code: int,
        packet_max_length: int,
    ) -> None:
        self.insert_into_vula = insert_into_vula
        self.max_age = max_age
        self.packet_max_length = packet_max_length
        self.log: Logger = getLogger()
        self.socket = socket.socket(
            socket.PF_PACKET,
            socket.SOCK_RAW,
            socket.htons(arp_code),  # maybe filter by packet type
        )
        # self.socket.setblocking(False)
        self.socket.settimeout(1)
        self.active = False
        self.peers_lock = threading.Lock()
        self.peers: dict = {}
        self.sniffing_thread: threading.Thread
        self.packet_queue_lock = threading.Lock()
        self.packet_queue: Queue = Queue()
        self.descriptor_queue_lock = threading.Lock()
        self.descriptor_queue: Queue = Queue()
        self.bus = pydbus.SystemBus()
        self.organize = self.bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)

    def receive_packet(self) -> bool:
        """
        Listens on the network for ARP packets
        and adds them into the packet queue.
        """
        self.log.debug("receive_packet")
        with self.packet_queue_lock:
            try:
                packet = self.socket.recvfrom(self.packet_max_length)
                self.packet_queue.put(packet)
                return True
            except socket.error:
                pass
        time.sleep(0)  # XXX TODO: do we still need this?
        return False

    def flush_old_peers(self) -> None:
        """
        Flush stale packet streams by clearing out the data structure
        """
        self.log.debug("flush_old_peers")
        t = time.time()
        with self.peers_lock:
            for src_mac in self.peers.keys():
                if t - self.peers[src_mac]["updated"] > self.max_age:
                    self.log.debug("New packet stream detected, clearing data")
                    self.peers[src_mac]["byte_stream"] = b""

    def update_peer(
        self, t: float, src_mac: bytes, candidate: Optional[bytes]
    ) -> None:
        """
        Update the peer by appeding the valid candidate bytes to the byte
        stream and pdating the timestamp.
        """
        self.log.debug("update_peer")
        with self.peers_lock:
            if candidate is None:
                self.peers[src_mac] = {"byte_stream": b"", "updated": t}
                return
            if src_mac not in self.peers:
                self.peers[src_mac] = {"byte_stream": b"", "updated": t}
            self.peers[src_mac]["updated"] = t
            self.log.debug("Received packet")
            self.peers[src_mac]["byte_stream"] += candidate

    def decrypt_all_broadcasts(self) -> None:
        """
        Try to decrypt the packetstream of all entries.
        Add descriptor into queue if succesfull
        """
        self.log.debug("decrypt_all_broadcasts")
        erase_list = []
        with self.peers_lock:
            for src_mac in self.peers.keys():
                descriptor = self.decrypt_broadcast(src_mac)
                if descriptor is not None:
                    self.log.info(
                        f"inserting into descriptor queue {descriptor}"
                    )
                    self.descriptor_queue.put(descriptor)
                    erase_list.append(src_mac)
                else:
                    continue
        now = time.time()
        for src_mac in erase_list:
            self.update_peer(now, src_mac, None)

    def decrypt_broadcast(self, src_mac: bytes) -> Optional[str]:
        """
        Start decryption process
        """
        self.log.debug("decrypt_broadcast")
        return self.decrypt(self.peers[src_mac]["byte_stream"], src_mac)

    def process_descriptors(self) -> bool:
        """
        Empty out descriptor queue by sending them to organize.
        """
        self.log.debug("process_descriptors")
        try:
            descriptor = self.descriptor_queue.get_nowait()
            if self.insert_into_vula:
                self.log.debug(
                    "Inserting descriptor into vula. Descriptor: "
                    + str(descriptor)
                )
                self.organize.process_descriptor_string(descriptor)
                return True
            else:
                self.log.info(descriptor)
                return True
        except Empty:
            return False

    def process_packet(self) -> bool:
        """
        Empty out packet queue and process them
        """
        self.log.debug("process_packet")
        try:
            packet = self.packet_queue.get_nowait()
            candidate = packet[0][42:]
            if candidate[0] != 0 and len(candidate) == PAYLOAD_MAX_SIZE:
                src_mac = packet[0][22:28]
                now = int(time.time())
                self.update_peer(now, src_mac, candidate)
                return True
            else:
                del packet
                del candidate
        except Empty:
            return False
        finally:
            time.sleep(0)
            return False

    def capture(self) -> None:
        """
        Capture thread main body. Captures and processes packets.
        Updates descriptor queue for processing
        """
        self.log.debug("starting capture")
        while self.active:
            self.receive_packet()
            self.log.debug("received packets")
            self.process_packet()
            self.log.debug("processed packets")
            time.sleep(0.5)
        self.log.debug("stopping capture")

    def process(self) -> None:
        """
        Processing thread main body. Processes all packets in queue
        """
        self.log.debug("starting processing")
        while self.active:
            self.decrypt_all_broadcasts()
            self.process_descriptors()
            self.log.debug("processed descriptors")
            time.sleep(0.5)
        self.log.debug("stopping process")

    def flush(self) -> None:
        """
        Flushing thread main body. Clean up datastructure.
        """
        self.log.debug("flush")
        while self.active:
            self.flush_old_peers()
            time.sleep(0.5)
        self.log.debug("stopping flush")

    def decrypt(self, message: bytes, key: bytes) -> Optional[str]:
        """
        Decrypts and decompresses message with given key
        """
        self.log.debug("decrypt")
        key = hashlib.sha256(key).digest()
        box = nacl.secret.SecretBox(key)
        try:
            decrypt = box.decrypt(message.strip(b"\x00"))
            decrypt = zlib.decompress(decrypt)
            if decrypt[10:15] == b"addrs":
                return str(decrypt[10:], "utf-8")
            else:
                return None
        except nacl.exceptions.CryptoError:
            return None

    def start(self) -> None:
        """
        DBus exposed controlling function. Starts the whole process
        """
        self.log.info("Starting alternative discovery")
        self.active = True
        self.sniffing_thread = threading.Thread(target=self.capture)
        self.sniffing_thread.start()
        self.processing_thread = threading.Thread(target=self.process)
        self.processing_thread.start()
        self.flushing_thread = threading.Thread(target=self.flush)
        self.flushing_thread.start()

    def stop(self) -> None:
        """
        DBus exposed controlling function. Stops the whole process
        """
        self.log.info("Stopping alternative discovery")
        click.echo(self.active)
        self.active = False
        click.echo(self.active)

    @classmethod
    def daemon(
        cls,
        insert_into_vula: bool,
        max_age: int,
        arp_code: int,
        packet_max_length: int,
    ) -> None:
        """
        Set up DBus and init object
        """
        loop = GLib.MainLoop()

        discover = cls(insert_into_vula, max_age, arp_code, packet_max_length)

        discover.log.info("dbus enabled")
        system_bus = pydbus.SystemBus()
        system_bus.publish(_DISCOVER_ALT_DBUS_NAME, discover)

        loop.run()


@click.command(short_help="Layer 2 alternate discovery daemon")
@click.option(
    "--insert_into_vula",
    is_flag=True,
    default=True,
    help="Automatically insert into vula.",
)
@click.option(
    "--max_age",
    default=5,
    type=int,
    help="Maximum amount of seconds in between each packet.",
)
@click.option(
    "--arp_code",
    default=0x0806,
    type=int,
    help="EtherType to be used in header",
)
@click.option(
    "--packet_max_length",
    default=60,
    type=int,
    help="Max length of packet to capture",
)
def main(
    insert_into_vula: bool, max_age: int, arp_code: int, packet_max_length: int
) -> None:

    Discover_Alt.daemon(insert_into_vula, max_age, arp_code, packet_max_length)


if __name__ == "__main__":
    main()
