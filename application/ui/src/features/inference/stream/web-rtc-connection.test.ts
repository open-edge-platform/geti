// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { HttpResponse } from 'msw';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { WebRTCConnection } from './web-rtc-connection';

describe('WebRTCConnection', () => {
    let connection: WebRTCConnection;

    beforeEach(() => {
        connection = new WebRTCConnection();
    });

    afterEach(async () => {
        try {
            await connection.stop();
        } finally {
            rs.unstubAllGlobals();
        }
    });

    it.each([true, false])('handles connection establishment with immediate=%s', async (immediate) => {
        class PeerConnection extends EventTarget {
            connectionState: RTCPeerConnectionState = 'new';
            iceGatheringState = 'complete';
            localDescription = { type: 'offer', sdp: 'offer' };
            addTransceiver = rs.fn();
            createDataChannel = rs.fn().mockReturnValue({ send: rs.fn() });
            createOffer = rs.fn().mockResolvedValue(this.localDescription);
            setLocalDescription = rs.fn();
            getTransceivers = rs.fn().mockReturnValue([]);
            getSenders = rs.fn().mockReturnValue([]);
            close = rs.fn();
            setRemoteDescription = rs.fn().mockImplementation(async () => {
                if (immediate) {
                    this.connect();
                }
            });

            connect() {
                this.connectionState = 'connected';
                this.dispatchEvent(new Event('connectionstatechange'));
            }
        }

        const peerConnection = new PeerConnection();
        rs.stubGlobal(
            'RTCPeerConnection',
            rs.fn(function () {
                return peerConnection;
            })
        );
        server.use(
            http.get('/api/webrtc/config', () => HttpResponse.json({ iceServers: [] })),
            http.post('/api/webrtc/offer', () => HttpResponse.json({ type: 'answer', sdp: 'answer' })),
            http.post('/api/webrtc/input_hook', () => HttpResponse.json({}))
        );
        const listener = rs.fn();
        connection.subscribe(listener);

        await connection.start();
        if (!immediate) {
            expect(connection.getStatus()).toBe('connecting');
            peerConnection.connect();
        }

        expect(connection.getStatus()).toBe('connected');
        expect(listener).toHaveBeenCalledWith({ type: 'status_change', status: 'connected' });
    });
});
