#!/usr/bin/env python3
"""
PyCyphal listener - receives broadcast messages on subject 1234
Run this in one terminal while main.py runs in another.
"""
import asyncio
import pycyphal
from pycyphal.transport.can import CANTransport
from pycyphal.transport.can.media.socketcan import SocketCANMedia
from pycyphal.transport import (
    PayloadMetadata,
    MessageDataSpecifier,
    InputSessionSpecifier
)
async def main():
    # -----------------------------
    # Setup CAN media (same interface as sender)
    # -----------------------------
    media = SocketCANMedia(
        iface_name="vcan0",   # Use vcan0 for virtual CAN testing
        mtu=64                # 64 bytes = CAN FD mode
    )
    # -----------------------------
    # Create CAN transport with DIFFERENT node ID
    # -----------------------------
    transport = CANTransport(
        media,
        local_node_id=43     # Different from sender (42)
    )
    try:
        # -----------------------------
        # Subscribe to subject 1234
        # -----------------------------
        data_spec = MessageDataSpecifier(subject_id=1234)
        session_spec = InputSessionSpecifier(data_spec, remote_node_id=None)
        sub = transport.get_input_session(session_spec, PayloadMetadata(64))
        print(":headphones: Listening for messages on subject 1234...")
        print("   (Press Ctrl+C to stop)")
        print()
        # Wait for messages (this will loop forever)
        while True:
            # receive() needs a deadline (current time + timeout in seconds)
            transfer = await sub.receive(asyncio.get_event_loop().time() + 1.0)
            if transfer is not None:
                payload = bytes(transfer.fragmented_payload[0])
                print(f":incoming_envelope: Received from Node {transfer.source_node_id}: {payload.decode('utf-8', errors='replace')}")
                print(f"   Priority: {transfer.priority}")
                print(f"   Transfer ID: {transfer.transfer_id}")
                print(f"   Timestamp: {transfer.timestamp}")
                print()
    except KeyboardInterrupt:
        print("\n:wave: Stopping listener...")
    finally:
        transport.close()
        await asyncio.sleep(0.1)
if __name__ == "__main__":
    asyncio.run(main())