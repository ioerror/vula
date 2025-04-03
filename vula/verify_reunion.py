import time
from typing import List, Optional

import click
from rendez.vous.reunion.multicast import UDPListeners

from .notclick import red


def reunion_multicast_run_verify(
    passphrase: str,
    message: bytes,
    interval: int,
    multicast_group: str,
    multicast_port: int,
    reveal_once: bool,
    bind_addr: str,
    bind_mask: List[str],
    timeout: int,
    hostname: str,
    verbose: bool,
) -> bytes:
    if reveal_once is not True:
        raise click.ClickException(
            "REUNION multi-reveal support is currently unavailable"
        )
    passphrase_b: bytes = passphrase.encode()
    udp: UDPListeners = UDPListeners(bind_addr, bind_mask, 0, verbose)
    udp.bind_multicast(multicast_group, multicast_port)

    started: Optional[float] = None
    msg: bool = False
    peer_payload: Optional[bytes] = None
    first_started: float = time.time()
    while not msg:
        if started is None or time.time() - started > interval:
            started = time.time()
            udp.new_session(passphrase_b, message)
            assert udp.session is not None
            udp.send(b"t1_", udp.session.t1, (multicast_group, multicast_port))
        elif time.time() - first_started > timeout:
            break
        udp.poll()
        udp.poll_multicast()
        if udp.peer_message is not None:
            msg = True
            peer_payload = udp.peer_message
            if len(peer_payload) != 32:
                click.echo(red("Hashed peer VK length incorrect"))
                raise click.ClickException("Verification failed")
            else:
                break
    if peer_payload is not None:
        return peer_payload
    else:
        raise click.ClickException("REUNION timeout reached")
