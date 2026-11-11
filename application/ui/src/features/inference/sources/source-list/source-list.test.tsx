// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import * as actualWebRtc from '../../stream/web-rtc-connection-provider' with { rstest: 'importActual' };
import { SourcesList } from './source-list.component';

rs.mock('../../stream/web-rtc-connection-provider', () => ({
    ...actualWebRtc,
    useWebRTCConnection: () => ({ stop: rs.fn() }),
}));

const ipCamera: IPCameraSourceConfig = {
    id: 'ip-id',
    name: 'Gate camera',
    source_type: 'ip_camera',
    stream_url: 'rtsp://gate.local/stream',
    auth_required: true,
};

describe('SourcesList', () => {
    it.each([
        {
            outcome: 'reachable',
            status: 200,
            body: { reachable: true, latency_ms: 5, error: null },
            badge: 'Ready',
        },
        {
            outcome: 'unreachable',
            status: 200,
            body: { reachable: false, latency_ms: null, error: 'Timeout' },
            badge: 'Unreachable',
        },
        {
            outcome: 'failing with a reason',
            status: 400,
            body: { detail: 'Camera refused the connection' },
            badge: 'Camera refused the connection',
        },
    ] as const)('marks a $outcome source after "Test connection" as "$badge"', async ({ status, body, badge }) => {
        server.use(
            http.get('/api/projects/{project_id}/pipeline', () =>
                HttpResponse.json(getMockedPipeline({ source: null, status: 'idle' }))
            ),
            http.post('/api/sources/{source_id}:test', () => HttpResponse.json(body as never, { status }))
        );
        render(<SourcesList sources={[ipCamera]} onAddSource={rs.fn()} onEditSource={rs.fn()} />);

        const card = within(await screen.findByTestId(`source-card-${ipCamera.name}`));
        expect(card.queryByText(badge)).not.toBeInTheDocument();

        await userEvent.click(card.getByRole('button', { name: /source menu/i }));
        await userEvent.click(screen.getByRole('menuitem', { name: 'Test connection' }));

        expect(await card.findByText(badge)).toBeVisible();
    });
});
