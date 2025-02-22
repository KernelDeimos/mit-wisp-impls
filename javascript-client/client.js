import putility from '@heyputer/putility';
import Websocket from 'ws';

const WispPacketType = {
    CONNECT: 1,
    DATA: 2,
    CONTINUE: 3,
    CLOSE: 4,
    INFO: 5,
};

const create_wisp_packet = ({
    streamId,
    packetType,
    payload
}) => {
    const size = 5 + payload.length;

    const data = new Uint8Array(size);
    const view = new DataView(data.buffer);
    view.setUint8(0, packetType);
    view.setUint32(1, streamId, true);
    data.set(payload, 5);

    return data;
};

const parse_wisp_packet = (data) => {
    const view = new DataView(data.buffer);
    const packetType = view.getUint8(0);
    const streamId = view.getUint32(1, true);
    const payload = data.slice(5);

    return {
        packetType,
        streamId,
        payload,
    };
}

const create_info_payload = ({
    majorVersion,
    minorVersion,
    extensionData,
}) => {
    const size = 2 + extensionData.length;

    const data = new Uint8Array(size);
    const view = new DataView(data.buffer);
    view.setUint8(0, majorVersion);
    view.setUint8(1, minorVersion);
    data.set(extensionData, 2);

    return data;
};

const parse_info_payload = (data) => {
    console.log('parse_info_payload', data.constructor.name);

    const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
    const majorVersion = view.getUint8(0);
    console.log('majorVersion', majorVersion);
    const minorVersion = view.getUint8(1);
    const extensionData = data.slice(2);

    return {
        majorVersion,
        minorVersion,
        extensionData,
    };
}

const main = async () => {
    const closed = new putility.libs.promise.TeePromise();

    let state = null;
    const STATE_INFO = {
        handle_message (message) {

            const received = parse_wisp_packet(message);

            if ( received.packetType === WispPacketType.CLOSE ) {
                console.log('Server closed connection');
                ws.close();
                closed.resolve();
                return;
            }

            if ( received.packetType !== WispPacketType.INFO ) {
                console.log('Invalid packet type');
                return;
            }

            const info = parse_info_payload(received.payload);
            console.log('Server info: ', info);

            if ( info.majorVersion !== 2 ) {
                console.log('Unsupported major version');
                // Send CLOSE packet
                const packet = create_wisp_packet({
                    streamId: 0,
                    packetType: WispPacketType.CLOSE,
                    payload: new Uint8Array([0x04]),
                });
                ws.send(packet);

                ws.close();
                closed.resolve();
                return;
            }

            const packet = create_wisp_packet({
                streamId: 0,
                packetType: WispPacketType.INFO,
                payload: create_info_payload({
                    majorVersion: 2,
                    minorVersion: 0,
                    extensionData: new Uint8Array(0),
                }),
            });

            ws.send(packet);
            state = STATE_CONTINUE;
        }
    };
    const STATE_CONTINUE = {
        handle_message (message) {
            state = STATE_DATA;
        }
    };
    const STATE_DATA = {
        handle_message (message) {
            // TODO
            console.log('data state not implemented');
        }
    };
    state = STATE_INFO;

    const ws = new Websocket('ws://localhost:8765');

    ws.on('open', () => {
        console.log('Connected to server');
    })

    ws.on('close', () => {
        console.log('Disconnected from server');
        closed.resolve();
    })

    ws.on('message', async (data) => {
        console.log('From Server: ', data);
        state.handle_message(data);
    });

    await closed;
};

main();
