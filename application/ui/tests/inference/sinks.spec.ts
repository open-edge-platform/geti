// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig, MqttSinkConfig, WebhookSinkConfig } from '@/api/types';
import { HttpResponse } from 'msw';

import { expect, http, test } from '../fixtures';
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

        test('leaves the rate limit unset when it is not filled in', async ({ inferencePage, sinksPage, page }) => {
            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Folder');

            await page.getByRole('textbox', { name: 'Folder Path' }).fill('/data/snapshots');
            await sinksPage.selectOutputFormats(['Predictions']);
            await sinksPage.getAddAndUseButton().click();

            await expect(sinksPage.getSinkCard('Local folder sink').getByText('Rate limit: Not set')).toBeVisible();
        });

        test('adds a webhook sink with custom headers', async ({ inferencePage, sinksPage, page }) => {
            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Webhook');

            await expect(sinksPage.getNameField()).toHaveValue('Webhook sink');

            await sinksPage.fillRateLimit(2, 1);
            await sinksPage.selectHttpMethod('PUT');
            await page.getByRole('textbox', { name: 'Timeout' }).fill('10');
            await page.getByRole('textbox', { name: 'Webhook URL' }).fill('https://hooks.local/geti');
            await sinksPage.selectOutputFormats(['Image with Predictions']);
            await sinksPage.addWebhookHeader('X-Removed', 'gone');
            await sinksPage.addWebhookHeader('X-Api-Key', 'secret');
            await page.getByRole('button', { name: 'Remove', exact: true }).first().click();
            await sinksPage.getAddAndUseButton().click();

            await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeVisible();

            const card = sinksPage.getSinkCard('Webhook sink');
            await expect(card.getByText('webhook', { exact: true })).toBeVisible();
            await expect(card.getByText('Rate limit: 2 samples every 1 second')).toBeVisible();
            await expect(card.getByText('HTTP method: PUT')).toBeVisible();
            await expect(card.getByText('Timeout: 10')).toBeVisible();
            await expect(card.getByText('Webhook URL: https://hooks.local/geti')).toBeVisible();
            await expect(card.getByText('X-Api-Key: secret')).toBeVisible();
            await expect(card.getByText('X-Removed: gone')).toBeHidden();
            await expect(card.getByText('image with predictions', { exact: true })).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();
        });

        test('does not add a webhook sink with a header that has no value', async ({
            inferencePage,
            sinksPage,
            page,
        }) => {
            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Webhook');

            await page.getByRole('textbox', { name: 'Webhook URL' }).fill('https://hooks.local/geti');
            await sinksPage.selectOutputFormats(['Predictions']);
            await sinksPage.addWebhookHeader('X-Api-Key', '');
            await expect(sinksPage.getAddAndUseButton()).toBeDisabled();
            await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeHidden();

            await sinksPage.openSinkList();
            await expect(sinksPage.getSinkCards()).toHaveCount(0);
        });

        test('does not add a webhook sink with duplicate header keys', async ({ inferencePage, sinksPage, page }) => {
            // Expected: the duplicate key is rejected.

            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Webhook');

            await page.getByRole('textbox', { name: 'Webhook URL' }).fill('https://hooks.local/geti');
            await sinksPage.selectOutputFormats(['Predictions']);
            await sinksPage.addWebhookHeader('X-Key', 'first');
            await sinksPage.addWebhookHeader('X-Key', 'second');

            await expect(page.getByRole('textbox', { name: 'headers-keys' }).last()).toHaveAttribute(
                'aria-invalid',
                'true'
            );
            await expect(sinksPage.getAddAndUseButton()).toBeDisabled();
            await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeHidden();

            await sinksPage.openSinkList();
            await expect(sinksPage.getSinkCards()).toHaveCount(0);
        });

        test('adds an MQTT sink that requires authentication', async ({ inferencePage, sinksPage, page }) => {
            await inferencePage.goto();
            await sinksPage.openAddSinkForm('MQTT');

            await expect(sinksPage.getNameField()).toHaveValue('MQTT sink');

            await page.getByRole('textbox', { name: 'Broker Host' }).fill('mqtt.local');
            await page.getByRole('textbox', { name: 'Topic' }).fill('line-1/predictions');
            await page.getByRole('textbox', { name: 'Broker Port' }).fill('8883');
            await page.getByRole('switch', { name: 'Require Authentication' }).click();
            await sinksPage.selectOutputFormats(['Predictions']);
            await sinksPage.getAddAndUseButton().click();

            await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeVisible();

            const card = sinksPage.getSinkCard('MQTT sink');
            await expect(card.getByText('mqtt', { exact: true })).toBeVisible();
            await expect(card.getByText('Broker host: mqtt.local')).toBeVisible();
            await expect(card.getByText('Broker port: 8883')).toBeVisible();
            await expect(card.getByText('Topic: line-1/predictions')).toBeVisible();
            await expect(card.getByText('Auth required: Yes')).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();
        });

        const requiredFieldCases = [
            { type: 'Folder', requiredField: 'Folder Path' },
            { type: 'Webhook', requiredField: 'Webhook URL' },
            { type: 'MQTT', requiredField: 'Broker Host' },
        ] as const;

        for (const { type, requiredField } of requiredFieldCases) {
            test(`does not add a ${type} sink without "${requiredField}"`, async ({ inferencePage, sinksPage }) => {
                await inferencePage.goto();
                await sinksPage.openAddSinkForm(type);

                await sinksPage.selectOutputFormats(['Predictions']);
                await expect(sinksPage.getAddAndUseButton()).toBeDisabled();
                await expect(sinksPage.getAddAndUseButton()).toBeVisible();
                await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeHidden();

                await sinksPage.openSinkList();
                await expect(sinksPage.getSinkCards()).toHaveCount(0);
            });
        }

        test('does not add a sink without an output format', async ({ inferencePage, sinksPage, page }) => {
            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Folder');

            await page.getByRole('textbox', { name: 'Folder Path' }).fill('/data/snapshots');
            await expect(sinksPage.getAddAndUseButton()).toBeDisabled();
            await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeHidden();

            await sinksPage.openSinkList();
            await expect(sinksPage.getSinkCards()).toHaveCount(0);
        });

        test('shows the error and keeps the entered values when saving fails', async ({
            inferencePage,
            sinksPage,
            network,
            page,
        }) => {
            network.use(
                http.post('/api/sinks', () => {
                    // @ts-expect-error The 400 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Folder is not writable' }, { status: 400 });
                })
            );

            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Folder');
            await page.getByRole('textbox', { name: 'Folder Path' }).fill('/root');
            await sinksPage.fillRateLimit(3, 1);
            await sinksPage.selectOutputFormats(['Predictions']);
            await sinksPage.getAddAndUseButton().click();

            await expect(sinksPage.getToast('Failed to save sink configuration, Folder is not writable')).toBeVisible();
            await expect(page.getByRole('textbox', { name: 'Folder Path' })).toHaveValue('/root');
            await expect(page.getByRole('checkbox', { name: 'Predictions', exact: true })).toBeChecked();
            await expect(page.getByRole('textbox', { name: 'Samples' })).toHaveValue('3');
            await expect(page.getByRole('textbox', { name: 'Seconds' })).toHaveValue('1');

            await sinksPage.openSinkList();
            await expect(sinksPage.getSinkCards()).toHaveCount(0);
        });

        test('keeps the form open when the new sink cannot be connected', async ({
            inferencePage,
            sinksPage,
            network,
            page,
        }) => {
            network.use(
                http.patch('/api/projects/{project_id}/pipeline', () => {
                    // @ts-expect-error The 409 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Pipeline is busy' }, { status: 409 });
                })
            );

            await inferencePage.goto();
            await sinksPage.openAddSinkForm('Folder');
            await page.getByRole('textbox', { name: 'Folder Path' }).fill('/data/snapshots');
            await sinksPage.selectOutputFormats(['Predictions']);
            await sinksPage.getAddAndUseButton().click();

            await expect(sinksPage.getToast('Sink configuration created successfully.')).toBeVisible();
            await expect(sinksPage.getToast('Pipeline is busy').first()).toBeVisible();
            await expect(sinksPage.getAddAndUseButton()).toBeVisible();
            await expect(sinksPage.getNameField()).toBeVisible();
            await expect(page.getByRole('textbox', { name: 'Folder Path' })).toBeVisible();
            await expect(sinksPage.getSinkCards()).toHaveCount(0);

            await sinksPage.openSinkList();
            await expect(sinksPage.getSinkCard('Local folder sink').getByText('In use')).toBeHidden();
        });
    });

    test('lists every sink type with its settings, connected sink first', async ({
        inferencePage,
        sinksPage,
        network,
    }) => {
        network.use(
            ...createPipelineBackend({
                sinks: [folderSink, webhookSink, mqttSink],
                pipeline: { sink: mqttSink },
            }).handlers
        );

        await inferencePage.goto();
        await inferencePage.getSinkTab().click();

        await expect(sinksPage.getSinkCards()).toHaveCount(3);
        await expect(sinksPage.getSinkCards().first()).toHaveAttribute('data-testid', `sink-card-${mqttSink.name}`);

        const mqttCard = sinksPage.getSinkCard(mqttSink.name);
        await expect(mqttCard.getByText('In use')).toBeVisible();
        await expect(mqttCard.getByText('Topic: geti/predictions')).toBeVisible();
        await expect(mqttCard.getByText('Rate limit: Not set')).toBeVisible();
        await expect(mqttCard.getByText('Auth required: No')).toBeVisible();
        await expect(mqttCard.getByText('Broker host: broker.local')).toBeVisible();
        await expect(mqttCard.getByText('Broker port: 1883')).toBeVisible();
        await expect(mqttCard.getByText('image with predictions', { exact: true })).toBeVisible();

        const folderCard = sinksPage.getSinkCard(folderSink.name);
        await expect(folderCard.getByText('In use')).toBeHidden();
        await expect(folderCard.getByText('Folder path: /data/results')).toBeVisible();
        await expect(folderCard.getByText('Rate limit: 1 sample every 5 seconds')).toBeVisible();
        await expect(folderCard.getByText('predictions', { exact: true })).toBeVisible();
        await expect(folderCard.getByText('image original', { exact: true })).toBeVisible();

        const webhookCard = sinksPage.getSinkCard(webhookSink.name);
        await expect(webhookCard.getByText('Rate limit: 2 samples every 1 second')).toBeVisible();
        await expect(webhookCard.getByText('HTTP method: POST')).toBeVisible();
        await expect(webhookCard.getByText('Timeout: 5')).toBeVisible();
        await expect(webhookCard.getByText('Webhook URL: https://hooks.local/alerts')).toBeVisible();
        await expect(webhookCard.getByText('Authorization: Bearer token')).toBeVisible();
    });

    test.describe('sink menu', () => {
        test('connects a sink to the pipeline', async ({ inferencePage, sinksPage, network }) => {
            network.use(
                ...createPipelineBackend({ sinks: [folderSink, webhookSink], pipeline: { sink: folderSink } }).handlers
            );

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(webhookSink.name, 'Connect');

            await expect(sinksPage.getToast(`Successfully connected to "${webhookSink.name}"`)).toBeVisible();
            await expect(sinksPage.getSinkCard(webhookSink.name).getByText('In use')).toBeVisible();
            await expect(sinksPage.getSinkCard(folderSink.name).getByText('In use')).toBeHidden();
        });

        test('disconnects a sink without stopping the running pipeline', async ({
            inferencePage,
            sinksPage,
            network,
            page,
        }) => {
            network.use(
                ...createPipelineBackend({ sinks: [folderSink], pipeline: { sink: folderSink, status: 'running' } })
                    .handlers
            );

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(folderSink.name, 'Disconnect');

            await expect(page.getByRole('dialog')).toBeHidden();
            await expect(sinksPage.getToast(`Successfully disconnected from "${folderSink.name}"`)).toBeVisible();
            await expect(sinksPage.getSinkCard(folderSink.name).getByText('In use')).toBeHidden();
            await expect(inferencePage.getPipelineSwitch('enabled')).toBeVisible();
        });

        test('does not allow removing or testing the connected sink', async ({ inferencePage, sinksPage, network }) => {
            network.use(...createPipelineBackend({ sinks: [folderSink], pipeline: { sink: folderSink } }).handlers);

            await inferencePage.goto();
            await sinksPage.openSinkMenu(folderSink.name);

            await expect(sinksPage.getMenuItem('Remove')).toBeDisabled();
            await expect(sinksPage.getMenuItem('Test connection')).toBeDisabled();
            await expect(sinksPage.getMenuItem('Connect')).toBeHidden();
        });

        test('removes a sink', async ({ inferencePage, sinksPage, network }) => {
            network.use(...createPipelineBackend({ sinks: [folderSink, mqttSink] }).handlers);

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(folderSink.name, 'Remove');

            await expect(sinksPage.getToast(`${folderSink.name} has been removed successfully!`)).toBeVisible();
            await expect(sinksPage.getSinkCard(folderSink.name)).toBeHidden();
            await expect(sinksPage.getSinkCard(mqttSink.name)).toBeVisible();
        });

        test('marks a reachable sink as ready', async ({ inferencePage, sinksPage, network }) => {
            network.use(...createPipelineBackend({ sinks: [mqttSink] }).handlers);

            await inferencePage.goto();
            await inferencePage.getSinkTab().click();

            const card = sinksPage.getSinkCard(mqttSink.name);
            await expect(card).toBeVisible();
            await expect(card.getByText('Ready')).toBeHidden();

            await sinksPage.selectSinkMenuAction(mqttSink.name, 'Test connection');

            await expect(card.getByText('Ready')).toBeVisible();
        });

        test('marks an unreachable sink', async ({ inferencePage, sinksPage, network }) => {
            network.use(...createPipelineBackend({ sinks: [mqttSink] }).handlers);
            network.use(
                http.post('/api/sinks/{sink_id}:test', () =>
                    HttpResponse.json({ reachable: false, latency_ms: null, error: 'Timeout' })
                )
            );

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(mqttSink.name, 'Test connection');

            await expect(sinksPage.getSinkCard(mqttSink.name).getByText('Unreachable')).toBeVisible();
        });

        test('shows the reason when the connection test fails', async ({ inferencePage, sinksPage, network }) => {
            network.use(...createPipelineBackend({ sinks: [mqttSink] }).handlers);
            network.use(
                http.post('/api/sinks/{sink_id}:test', () => {
                    // @ts-expect-error The 400 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Broker refused the connection' }, { status: 400 });
                })
            );

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(mqttSink.name, 'Test connection');

            await expect(sinksPage.getSinkCard(mqttSink.name).getByText('Broker refused the connection')).toBeVisible();
        });
    });

    test.describe('editing a sink', () => {
        const editCases = [
            {
                sink: folderSink,
                field: { name: 'Folder Path', value: folderSink.folder_path },
                newValue: '/data/archive',
                expectedSetting: 'Folder path: /data/archive',
            },
            {
                sink: webhookSink,
                field: { name: 'Webhook URL', value: webhookSink.webhook_url },
                newValue: 'https://hooks.local/v2',
                expectedSetting: 'Webhook URL: https://hooks.local/v2',
            },
            {
                sink: mqttSink,
                field: { name: 'Broker Host', value: mqttSink.broker_host },
                newValue: 'broker-2.local',
                expectedSetting: 'Broker host: broker-2.local',
            },
        ] as const;

        for (const { sink, field, newValue, expectedSetting } of editCases) {
            test(`edits a ${sink.sink_type} sink`, async ({ inferencePage, sinksPage, network, page }) => {
                network.use(...createPipelineBackend({ sinks: [sink] }).handlers);

                await inferencePage.goto();
                await sinksPage.selectSinkMenuAction(sink.name, 'Edit');

                await expect(page.getByText('Edit sink')).toBeVisible();

                const input = page.getByRole('textbox', { name: field.name });
                await expect(input).toHaveValue(field.value);

                await input.fill(newValue);
                await sinksPage.getSaveButton().click();

                await expect(sinksPage.getToast('Sink configuration updated successfully.')).toBeVisible();

                const card = sinksPage.getSinkCard(sink.name);
                await expect(card.getByText(expectedSetting)).toBeVisible();
                await expect(card.getByText('In use')).toBeHidden();
            });
        }

        test('edits the rate limit and output formats of a sink', async ({
            inferencePage,
            sinksPage,
            network,
            page,
        }) => {
            network.use(...createPipelineBackend({ sinks: [folderSink] }).handlers);

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(folderSink.name, 'Edit');

            await expect(page.getByRole('textbox', { name: 'Samples' })).toHaveValue('0.2');
            await expect(page.getByRole('textbox', { name: 'Seconds' })).toHaveValue('1');
            await expect(page.getByRole('checkbox', { name: 'Predictions', exact: true })).toBeChecked();
            await expect(page.getByRole('checkbox', { name: 'Image Original', exact: true })).toBeChecked();
            await expect(page.getByRole('checkbox', { name: 'Image with Predictions', exact: true })).not.toBeChecked();

            await sinksPage.fillRateLimit(3, 1);
            await page.getByRole('checkbox', { name: 'Image Original', exact: true }).uncheck();
            await sinksPage.selectOutputFormats(['Image with Predictions']);
            await sinksPage.getSaveButton().click();

            await expect(sinksPage.getToast('Sink configuration updated successfully.')).toBeVisible();

            const card = sinksPage.getSinkCard(folderSink.name);
            await expect(card.getByText('Rate limit: 3 samples every 1 second')).toBeVisible();
            await expect(card.getByText('predictions', { exact: true })).toBeVisible();
            await expect(card.getByText('image with predictions', { exact: true })).toBeVisible();
            await expect(card.getByText('image original', { exact: true })).toBeHidden();
        });

        test('changes the HTTP method of a webhook sink and adds a header next to the existing one', async ({
            inferencePage,
            sinksPage,
            network,
        }) => {
            network.use(...createPipelineBackend({ sinks: [webhookSink] }).handlers);

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(webhookSink.name, 'Edit');

            await sinksPage.selectHttpMethod('PATCH');
            await sinksPage.addWebhookHeader('X-Trace', 'on');
            await sinksPage.getSaveButton().click();

            await expect(sinksPage.getToast('Sink configuration updated successfully.')).toBeVisible();

            const card = sinksPage.getSinkCard(webhookSink.name);
            await expect(card.getByText('HTTP method: PATCH')).toBeVisible();
            await expect(card.getByText('Authorization: Bearer token')).toBeVisible();
            await expect(card.getByText('X-Trace: on')).toBeVisible();
        });

        test('removes an existing webhook header', async ({ inferencePage, sinksPage, network, page }) => {
            network.use(...createPipelineBackend({ sinks: [webhookSink] }).handlers);

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(webhookSink.name, 'Edit');

            await page.getByRole('button', { name: 'Remove', exact: true }).click();
            await sinksPage.getSaveButton().click();

            await expect(sinksPage.getToast('Sink configuration updated successfully.')).toBeVisible();
            await expect(sinksPage.getSinkCard(webhookSink.name).getByText('Authorization: Bearer token')).toBeHidden();
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

        test('shows the error and keeps the edited values when updating fails', async ({
            inferencePage,
            sinksPage,
            network,
            page,
        }) => {
            network.use(...createPipelineBackend({ sinks: [folderSink] }).handlers);
            network.use(
                http.patch('/api/sinks/{sink_id}', () => {
                    // @ts-expect-error The 400 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Folder is not writable' }, { status: 400 });
                })
            );

            await inferencePage.goto();
            await sinksPage.selectSinkMenuAction(folderSink.name, 'Edit');
            await page.getByRole('textbox', { name: 'Folder Path' }).fill('/root');
            await sinksPage.getSaveButton().click();

            await expect(sinksPage.getToast('Failed to save sink configuration, Folder is not writable')).toBeVisible();
            await expect(page.getByText('Edit sink')).toBeVisible();
            await expect(page.getByRole('textbox', { name: 'Folder Path' })).toHaveValue('/root');
        });
    });
});
