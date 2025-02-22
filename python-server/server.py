import asyncio
import websockets
from enum import Enum

class WispPacketType(Enum):
    CONNECT = 1
    DATA = 2
    CONTINUE = 3
    CLOSE = 4
    INFO = 5

async def create_wisp_packet(
    streamId: int,
    packetType: WispPacketType,
    payload: bytes,
) -> bytes:
    # note: stream ID is a single byte
    # note: packet type is a 32-bit little-endian unsigned integer

    # create the header
    packet = bytearray()
    packet.append(packetType.value)
    packet += streamId.to_bytes(4, "little")

    # create the payload
    packet += payload

    return packet

async def parse_wisp_packet(packet: bytes):
    packetType = WispPacketType(packet[0])
    streamId = int.from_bytes(packet[1:5], "little")
    payload = packet[5:]
    return {
        "packetType": packetType,
        "streamId": streamId,
        "payload": payload,
    }

async def create_info_payload(
    majorVersion: int,
    minorVersion: int,
    extensionData: bytes,
) -> bytes:
    majorVersion = majorVersion.to_bytes(1, "little")
    minorVersion = minorVersion.to_bytes(1, "little")
    payload = majorVersion + minorVersion + extensionData
    return payload

async def parse_info_payload(payload: bytes):
    majorVersion = int.from_bytes(payload[0:1], "little")
    minorVersion = int.from_bytes(payload[1:2], "little")
    extensionData = payload[2:]
    return {
        "majorVersion": majorVersion,
        "minorVersion": minorVersion,
        "extensionData": extensionData,
    }

def create_close_packet(
    reason: int,
) -> bytes:
    return create_wisp_packet(
        streamId = 0,
        packetType = WispPacketType.CLOSE,
        payload = (reason).to_bytes(1)
    )

class StateHolder: # state of what state we are in
    def __init__(self, websocket):
        self.state = InfoState(self, websocket)

class InfoState:
    def __init__(self, state: StateHolder, websocket):
        self.state = state
        self.websocket = websocket
    async def handle_message(self, message: bytes):
        wispPacket = await parse_wisp_packet(message)

        if wispPacket["packetType"] == WispPacketType.CLOSE:
            self.state.state = ClosedState(self.state, self.websocket)
            # and close the connection
            self.websocket.close()
            return
        if wispPacket["packetType"] != WispPacketType.INFO:
            # send a close packet
            self.websocket.send(create_close_packet(0x01))
            # and close the connection
            self.websocket.close()
        
        # TODO: check required extensions here
        infoPayload = await parse_info_payload(wispPacket["payload"])
        print("Client Major Version: " + str(infoPayload["majorVersion"]))
        print("Client Minor Version: " + str(infoPayload["minorVersion"]))

        if infoPayload["majorVersion"] != 2:
            # send a close packet
            self.websocket.send(create_close_packet(0x04))
            # and close the connection
            self.websocket.close()

        # for now, close if any extension data is present
        if len(infoPayload["extensionData"]) > 0:
            # send a close packet
            self.websocket.send(create_close_packet(0x04))
            # and close the connection
            self.websocket.close()

        # send a continue packet
        await self.websocket.send(await create_wisp_packet(
            streamId = 0,
            packetType = WispPacketType.CONTINUE,
            payload = (0xFFFFFFFF).to_bytes(4, "little")
        ))

class ClosedState:
    def __init__(self, state: StateHolder, websocket):
        self.state = state
        self.websocket = websocket
    async def handle_message(self, message: bytes):
        pass

class DataState:
    def __init__(self, state: StateHolder, websocket):
        self.state = state
        self.websocket = websocket
    async def handle_message(self, message: bytes):
        # TODO
        print("Not implemented")

async def handle_connection(websocket):
    state_holder = StateHolder(websocket)

    await websocket.send(await create_wisp_packet(
        streamId = 0,
        packetType = WispPacketType.INFO,
        payload = await create_info_payload(
            majorVersion = 2,
            minorVersion = 0,
            extensionData = b"",
        ),
    ))

    # anon object with methods
    async for message in websocket:
        print("From Client: " + message.hex(' '))
        await state_holder.state.handle_message(message)

async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
