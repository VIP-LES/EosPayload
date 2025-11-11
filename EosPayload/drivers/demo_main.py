#!/usr/bin/env python3
"""
Minimal PyCyphal test on Python 3.13 + PyCyphal 1.24.x
Sends a single broadcast CAN FD message on can0.
"""
import asyncio
import pycyphal
from pycyphal.transport.can import CANTransport
from pycyphal.transport.can.media.socketcan import SocketCANMedia
from pycyphal.transport import (
    PayloadMetadata,
    MessageDataSpecifier,
    OutputSessionSpecifier,
    Transfer,
    Priority,
    Timestamp
)
async def main():
    # -----------------------------
    # Setup CAN media
    # -----------------------------
    media = SocketCANMedia(
        iface_name="vcan0",  # Virtual CAN for testing (use "can0" for real hardware)
        mtu=64               # 64 bytes = CAN FD mode
    )
    # -----------------------------
    # Create CAN transport
    # -----------------------------
    transport = CANTransport(
        media,
        local_node_id=42     # unique node ID on your bus (1–127)
    )
    try:
        # -----------------------------
        # Define broadcast subject
        # -----------------------------
        data_spec = MessageDataSpecifier(subject_id=1234)  # subject ID for broadcast
        # Wrap in OutputSessionSpecifier for broadcast (remote_node_id=None)
        session_spec = OutputSessionSpecifier(data_spec, remote_node_id=None)
        # -----------------------------
        # Create output session
        # -----------------------------
        pub = transport.get_output_session(
            session_spec,
            PayloadMetadata(64)   # payload buffer size in bytes
        )
        # -----------------------------
        # Create a simple transfer
        # -----------------------------
        transfer = Transfer(
            timestamp=Timestamp.now(),
            priority=Priority.NOMINAL,
            transfer_id=0,
            fragmented_payload=[memoryview(b"Hello FD world!")]
        )
        # -----------------------------
        # Send the transfer (async operation)
        # -----------------------------
        await pub.send(transfer, asyncio.get_event_loop().time() + 1.0)
        print("Sent CAN FD frame on can0 successfully!")
    finally:
        # -----------------------------
        # Cleanup: close the transport
        # -----------------------------
        transport.close()
        await asyncio.sleep(0.1)  # Allow cleanup to complete
if __name__ == "__main__":
    asyncio.run(main())