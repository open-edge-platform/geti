// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig, MqttSinkConfig, WebhookSinkConfig } from '@/api/types';

import { expect, test } from '../fixtures';
import { createPipelineBackend } from './pipeline-backend';

const folderSink: LocalFolderSinkConfig = {
    id: 'folder-sink-id',
    name: 'Results folder',
    sink_type: 'folder',
    folder_path: '/data/results',
    rate_limit: 0.2,
    output_formats: ['predictions', 'image_original'],
};

const webhookSink: WebhookSinkConfig = {
    id: 'webhook-sink-id',
    name: 'Alerts webhook',
    sink_type: 'webhook',
    webhook_url: 'https://hooks.local/alerts',
    http_method: 'POST',
    headers: { Authorization: 'Bearer token' },
    timeout: 5,
    rate_limit: 2,
    output_formats: ['predictions'],
};

const mqttSink: MqttSinkConfig = {
    id: 'mqtt-sink-id',
    name: 'Factory broker',
    sink_type: 'mqtt',
    broker_host: 'broker.local',
    broker_port: 1883,
    topic: 'geti/predictions',
    auth_required: false,
    rate_limit: null,
    output_formats: ['image_with_predictions'],
};

test.describe('Pipeline sinks', () => {
    test.describe('adding a sink', () => {
        test.beforeEach(({ network }) => {
            network.use(...createPipelineBackend().handlers);
        });

        test('adds a folder sink and connects it to the pipeline', async ({ inferencePage, sinksPage, page }) => {
            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Folder');

            await expect(sinksPage.getNameField()).toHaveValue('Local folder sink');

            await sinksPage.getNameField().fill('Snapshots');
            await page.getByRole('textbox', { name: 'Folder Path' }).fill('/data/snapshots');
            await sinksPage.fillRateLimit(1, 5);
            await sinksPage.selectOutputFormats(['Predictions', 'Image Original']);
            await sinksPage.getAddAndUseButton().click();

            await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeVisible();

            const card = sinksPage.getSinkCard('Snapshots');
            await expect(card.getByText('folder', { exact: true })).toBeVisible();
            await expect(card.getByText('Folder path: /data/snapshots')).toBeVisible();
            await expect(card.getByText('Rate limit: 1 sample every 5 seconds')).toBeVisible();
            await expect(card.getByText('predictions', { exact: true })).toBeVisible();
            await expect(card.getByText('image original', { exact: true })).toBeVisible();
            await expect(card.getByText('image with predictions', { exact: true })).toBeHidden();
            await expect(card.getByText('In use')).toBeVisible();
        });
    });

    test.describe('sink menu', () => {
        test('connects a sink to the pipeline and disconnects it without stopping the running pipeline', async ({
            inferencePage,
            sinksPage,
            network,
            page,
        }) => {
            network.use(
                ...createPipelineBackend({
                    sinks: [folderSink, webhookSink],
                    pipeline: { sink: folderSink, status: 'running' },
                }).handlers
            );

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(webhookSink.name, 'Connect');

            await expect(sinksPage.getSinkCard(webhookSink.name).getByText('In use')).toBeVisible();
            await expect(sinksPage.getSinkCard(folderSink.name).getByText('In use')).toBeHidden();

            await sinksPage.selectSinkMenuAction(webhookSink.name, 'Disconnect');

            await expect(page.getByRole('dialog')).toBeHidden();
            await expect(sinksPage.getSinkCard(webhookSink.name).getByText('In use')).toBeHidden();
            await expect(sinksPage.getSinkCard(folderSink.name).getByText('In use')).toBeHidden();
            await expect(inferencePage.getPipelineSwitch('enabled')).toBeVisible();
        });

        test('removes a sink', async ({ inferencePage, sinksPage, network }) => {
            network.use(...createPipelineBackend({ sinks: [folderSink, mqttSink] }).handlers);

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(folderSink.name, 'Remove');

            await expect(sinksPage.getSinkCard(folderSink.name)).toBeHidden();
            await expect(sinksPage.getSinkCard(mqttSink.name)).toBeVisible();
        });
    });

    test.describe('editing a sink', () => {
        test('edits a folder sink', async ({ inferencePage, sinksPage, network, page }) => {
            network.use(...createPipelineBackend({ sinks: [folderSink] }).handlers);

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(folderSink.name, 'Edit');

            await expect(page.getByText('Edit sink')).toBeVisible();

            const input = page.getByRole('textbox', { name: 'Folder Path' });
            await expect(input).toHaveValue(folderSink.folder_path);

            await input.fill('/data/archive');
            await sinksPage.getSaveButton().click();

            await expect(sinksPage.getToast('Sink configuration updated successfully.')).toBeVisible();

            const card = sinksPage.getSinkCard(folderSink.name);
            await expect(card.getByText('Folder path: /data/archive')).toBeVisible();
            await expect(card.getByText('In use')).toBeHidden();
        });

        test('saves and connects an edited sink, then offers only "Save" for it', async ({
            inferencePage,
            sinksPage,
            network,
            page,
        }) => {
            network.use(
                ...createPipelineBackend({ sinks: [folderSink, mqttSink], pipeline: { sink: folderSink } }).handlers
            );

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(mqttSink.name, 'Edit');

            await page.getByRole('switch', { name: 'Require Authentication' }).click();
            await sinksPage.getSaveAndConnectButton().click();

            const card = sinksPage.getSinkCard(mqttSink.name);
            await expect(card.getByText('Auth required: Yes')).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();
            await expect(sinksPage.getSinkCard(folderSink.name).getByText('In use')).toBeHidden();

            await sinksPage.selectSinkMenuAction(mqttSink.name, 'Edit');

            await expect(sinksPage.getSaveButton()).toBeVisible();
            await expect(sinksPage.getSaveAndConnectButton()).toBeHidden();
        });
    });
});
