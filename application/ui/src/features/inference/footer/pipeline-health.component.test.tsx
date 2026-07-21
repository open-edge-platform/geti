// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { PipelineHealth as PipelineHealthType } from '@/api/types';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipelineHealth, getMockedStatus } from 'mocks/mock-pipeline-health';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { PipelineHealth } from './pipeline-health.component';

const CONTEXTUAL_HELP_TRIGGER_NAME = 'Pipeline component health';

const renderApp = (health: PipelineHealthType) => {
    server.use(http.get('/api/projects/{project_id}/pipeline/health', () => HttpResponse.json(health)));

    return render(<PipelineHealth />);
};

describe('PipelineHealth', () => {
    it('shows "Running" without a contextual-help trigger when there are no component messages', async () => {
        renderApp(
            getMockedPipelineHealth({
                status: 'running',
                components: {
                    source: getMockedStatus({ status: 'ok', message: null }),
                    sink: getMockedStatus({ status: 'ok', message: null }),
                    model: getMockedStatus({ status: 'ok', message: null }),
                },
            })
        );

        expect(await screen.findByRole('status')).toHaveTextContent('Running');
        expect(screen.queryByRole('button', { name: CONTEXTUAL_HELP_TRIGGER_NAME })).not.toBeInTheDocument();
    });

    it('shows "Idle" without a contextual-help trigger and without components', async () => {
        renderApp(getMockedPipelineHealth({ status: 'idle', components: null }));

        expect(await screen.findByRole('status')).toHaveTextContent('Idle');
        expect(screen.queryByRole('button', { name: CONTEXTUAL_HELP_TRIGGER_NAME })).not.toBeInTheDocument();
    });

    it('shows "Problems detected" with a contextual-help trigger when a component has a message', async () => {
        renderApp(
            getMockedPipelineHealth({
                status: 'error',
                components: {
                    source: getMockedStatus({ status: 'error', message: 'Camera disconnected' }),
                    sink: getMockedStatus({ status: 'ok' }),
                    model: getMockedStatus({ status: 'ok' }),
                },
            })
        );

        expect(await screen.findByRole('status')).toHaveTextContent('Problems detected');

        await userEvent.click(await screen.findByRole('button', { name: CONTEXTUAL_HELP_TRIGGER_NAME }));

        const popover = await screen.findByRole('dialog');

        expect(within(popover).getByText('Camera disconnected')).toBeVisible();
        expect(within(popover).getAllByText('Healthy')).toHaveLength(2);
    });

    it('does not show a contextual-help trigger when error status has no component messages', async () => {
        renderApp(
            getMockedPipelineHealth({
                status: 'error',
                components: {
                    source: getMockedStatus({ status: 'error', message: null }),
                    sink: getMockedStatus({ status: 'ok' }),
                    model: getMockedStatus({ status: 'ok' }),
                },
            })
        );

        expect(await screen.findByRole('status')).toHaveTextContent('Problems detected');
        expect(screen.queryByRole('button', { name: CONTEXTUAL_HELP_TRIGGER_NAME })).not.toBeInTheDocument();
    });
});
