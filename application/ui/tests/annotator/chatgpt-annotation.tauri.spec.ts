// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationDTO } from '@/api/types';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';

import { paths } from '../../src/constants/paths';
import { expect, http, test } from '../fixtures';
import { mockTauriRuntime } from '../utils/mock-tauri-runtime';
import { candyBinaryHandler, redLabel } from './annotator-fixtures';

const project = getMockedProject({
    id: '123e4567-e89b-12d3-a456-426614174000',
    task: { task_type: 'detection', exclusive_labels: true, labels: [redLabel] },
});

test.beforeEach(async ({ page, network }) => {
    await mockTauriRuntime(page);
    await page.addInitScript(() => {
        if (!localStorage.getItem('geti.ai-assistant.connection.v1'))
            localStorage.setItem(
                'geti.ai-assistant.connection.v1',
                JSON.stringify({ provider: 'chatgpt', model: '', executable: '' })
            );
        Object.assign(Reflect.get(window, '__TAURI_INTERNALS__') ?? {}, {
            transformCallback: () => 1,
            unregisterCallback: () => {},
            invoke: async (command: string, args: Record<string, unknown> = {}) => {
                if (command === 'openai_key_status') return false;
                if (command === 'codex_locate') return { path: 'codex.exe', searched: [] };
                if (command !== 'codex_operation') return null;
                if (args.operation === 'status') return { account: { email: 'test@example.com', planType: 'plus' } };
                if (args.operation === 'models')
                    return {
                        data: [
                            { id: 'astra-display-id', model: 'gpt-6-astra', displayName: 'GPT-6-Astra' },
                            { id: 'gpt-5.6-sol', model: 'gpt-5.6-sol', displayName: 'GPT-5.6-Sol' },
                        ],
                    };
                Reflect.set(window, 'lastRequestModel', (args.body as { model: string | null }).model);
                const body = args.body as {
                    input: { type: string }[];
                    tools: {
                        name: string;
                        parameters: {
                            properties: {
                                media_key: { enum: string[] };
                                annotations: { items: { properties: Record<string, unknown> } };
                            };
                        };
                    }[];
                };
                if (body.input.at(-1)?.type === 'function_call_output')
                    return {
                        text: '1 red-label annotation added to the image. Edit or Undo, then Submit to save.',
                        calls: [],
                    };
                const annotationTool = body.tools.find(({ name }) => name === 'propose_annotations');
                if (!annotationTool) return { text: 'I can see the attached image.', calls: [] };
                const fields = annotationTool.parameters.properties.annotations.items.properties;
                const shape =
                    'points' in fields
                        ? {
                              points: [
                                  { x: 100, y: 120 },
                                  { x: 300, y: 120 },
                                  { x: 200, y: 270 },
                              ],
                          }
                        : 'width' in fields
                          ? { x: 100, y: 120, width: 200, height: 150 }
                          : {};
                Reflect.set(
                    window,
                    'annotationImageWasSent',
                    JSON.stringify(body.input).includes('data:image/png;base64,')
                );
                return {
                    text: '',
                    calls: [
                        {
                            name: 'propose_annotations',
                            arguments: JSON.stringify({
                                media_key: annotationTool?.parameters.properties.media_key.enum[0],
                                annotations: [{ label_ids: ['red-label'], ...shape }],
                            }),
                        },
                    ],
                };
            },
        });
    });
    network.use(
        http.get('/api/projects/{project_id}', () => HttpResponse.json(project)),
        http.get('/api/projects', () => HttpResponse.json([project])),
        candyBinaryHandler,
        http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () =>
            HttpResponse.json({ annotations: [], user_reviewed: true, subset: 'training' })
        )
    );
});

for (const taskType of ['instance_segmentation', 'classification'] as const) {
    test(`applies and saves ${taskType} annotations`, async ({ page, annotatorPage, network }) => {
        let saved: AnnotationDTO[] = [];
        const taskProject = { ...project, task: { ...project.task, task_type: taskType } };
        network.use(
            http.get('/api/projects/{project_id}', () => HttpResponse.json(taskProject)),
            http.get('/api/projects', () => HttpResponse.json([taskProject])),
            http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ request }) => {
                saved = ((await request.json()) as { annotations: AnnotationDTO[] }).annotations;
                return HttpResponse.json({
                    annotations: saved,
                    media_id: 'item-1',
                    user_reviewed: true,
                    subset: 'training',
                });
            })
        );
        await annotatorPage.goto(project.id, 'item-1');
        await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
        const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
        await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
        await chat.getByRole('button', { name: 'Send', exact: true }).click();
        const layer = page.getByTestId('zoom-transform').getByTestId('annotation-layer');
        await expect(layer).toBeVisible();
        await expect(
            layer
                .getByLabel(taskType === 'classification' ? 'annotation full image' : 'annotation polygon', {
                    exact: true,
                })
                .filter({ visible: true })
        ).toBeVisible();
        await expect(chat.getByRole('button', { name: 'Apply to image' })).toHaveCount(0);
        await expect(chat).toBeVisible();
        await page.getByRole('button', { name: 'Submit', exact: true }).click();
        await expect.poll(() => saved.length).toBe(1);
        expect(saved[0]).toMatchObject({
            labels: [{ id: 'red-label' }],
            shape: { type: taskType === 'classification' ? 'full_image' : 'polygon' },
        });
    });
}

test('gallery annotation action opens the current-image chat in annotation mode', async ({ page }) => {
    await page.addInitScript(
        (id) => localStorage.setItem(`${id}-annotator-mode`, JSON.stringify('prediction')),
        project.id
    );
    await page.goto(paths.project.dataset.index({ projectId: project.id }));
    await page.getByRole('button', { name: 'More annotate options' }).click();
    await page.getByRole('menuitem', { name: 'Annotate with ChatGPT', exact: true }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    await expect(chat).toBeVisible();
    await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
    await expect(chat.getByText(/Current image:/)).toBeVisible();
});

test('project chat attaches a local image and accepts an image-only message', async ({ page }) => {
    await page.goto(paths.project.dataset.index({ projectId: project.id }));
    await page.getByRole('button', { name: 'More annotate options' }).click();
    await page.getByRole('menuitem', { name: 'Ask ChatGPT about this project' }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    await chat.locator('input[type=file]').setInputFiles('tests/assets/candy.png');
    await expect(chat.getByRole('img', { name: 'candy.png', exact: true })).toBeVisible();
    await chat.getByRole('button', { name: 'Send', exact: true }).click();
    await expect(chat.getByText('I can see the attached image.')).toBeVisible();
});

test('automatically adds editable annotations, keeps chat beside the image, undoes and saves', async ({
    page,
    annotatorPage,
    network,
}) => {
    let saved: AnnotationDTO[] = [];
    network.use(
        http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ request }) => {
            const body = (await request.json()) as { annotations: AnnotationDTO[] };
            saved = body.annotations;
            return HttpResponse.json({
                annotations: saved,
                media_id: 'item-1',
                user_reviewed: true,
                subset: 'training',
            });
        })
    );
    await annotatorPage.goto(project.id, 'item-1');
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
    await chat.getByRole('button', { name: 'Send', exact: true }).click();
    await expect(
        chat.getByText('1 red-label annotation added to the image. Edit or Undo, then Submit to save.')
    ).toBeVisible();
    await expect(chat.getByRole('button', { name: 'Apply to image' })).toHaveCount(0);
    const transform = page.getByTestId('zoom-transform');
    const layer = transform.getByTestId('annotation-layer');
    await expect(layer).toBeVisible();
    await expect(layer.locator('g[transform="translate(100, 120)"]').filter({ visible: true })).toBeVisible();
    await expect(layer.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
    expect(await page.evaluate(() => Reflect.get(window, 'annotationImageWasSent'))).toBe(true);
    expect(saved).toEqual([]);
    const imageBounds = await layer.boundingBox();
    const chatBounds = await chat.boundingBox();
    expect(imageBounds).not.toBeNull();
    expect(chatBounds).not.toBeNull();
    expect(imageBounds!.x + imageBounds!.width).toBeLessThanOrEqual(chatBounds!.x);
    await page.screenshot({ path: 'test-results/chatgpt-annotation-on-canvas.png' });
    const previousTransform = await transform.getAttribute('style');
    await page.mouse.move(imageBounds!.x + imageBounds!.width / 2, imageBounds!.y + imageBounds!.height / 2);
    await page.mouse.wheel(0, -150);
    await expect(transform).not.toHaveAttribute('style', previousTransform!);
    await expect(layer.locator('g[transform="translate(100, 120)"]').filter({ visible: true })).toBeVisible();
    await expect(chat).toBeVisible();
    await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
    await annotatorPage.undoAnnotation();
    await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(0);
    await annotatorPage.redoAnnotation();
    await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
    await page.getByRole('button', { name: 'Submit', exact: true }).click();
    await expect.poll(() => saved.length).toBe(1);
    expect(saved[0]).toMatchObject({
        labels: [{ id: 'red-label' }],
        shape: { type: 'rectangle', x: 100, y: 120, width: 200, height: 150 },
    });
});

test('automatically added annotations can be deleted using the editor', async ({ page, annotatorPage }) => {
    await annotatorPage.goto(project.id, 'item-1');
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
    await chat.getByRole('button', { name: 'Send', exact: true }).click();
    const label = page.getByTestId('annotation-layer').getByLabel(`label ${redLabel.name} background`, { exact: true });
    await expect(label).toHaveCount(1);
    await page
        .getByTestId('annotation-layer')
        .getByLabel('annotation rect', { exact: true })
        .filter({ visible: true })
        .click({ position: { x: 20, y: 20 } });
    await page.keyboard.press('Delete');
    await expect(label).toHaveCount(0);
    await annotatorPage.undoAnnotation();
    await expect(label).toHaveCount(1);
    await chat.getByRole('button', { name: 'Close', exact: true }).click();
    await expect(label).toHaveCount(1);
});

test('reopening chat retains sign-in while model discovery and chat share one native slot', async ({
    page,
    annotatorPage,
}) => {
    await annotatorPage.goto(project.id, 'item-1');
    await page.evaluate(() => {
        const internals = Reflect.get(window, '__TAURI_INTERNALS__');
        if (!internals) throw new Error('Missing desktop mock');
        const invoke = Reflect.get(internals, 'invoke') as (
            command: string,
            args: Record<string, unknown>
        ) => Promise<unknown>;
        const counts = { status: 0, conflicts: 0 };
        Reflect.set(window, 'codexOperationCounts', counts);
        let busy = false;
        Reflect.set(internals, 'invoke', async (command: string, args: Record<string, unknown>) => {
            if (command !== 'codex_operation') return invoke(command, args);
            if (busy) {
                counts.conflicts += 1;
                throw new Error('A ChatGPT operation is already running.');
            }
            if (args.operation === 'status') counts.status += 1;
            busy = true;
            try {
                await new Promise((resolve) => setTimeout(resolve, 150));
                return await invoke(command, args);
            } finally {
                busy = false;
            }
        });
    });
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    for (let count = 0; count < 3; count++) {
        await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
        await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
        await chat.getByRole('button', { name: 'Connection settings', exact: true }).click();
        await expect(chat.getByText('Signed in as test@example.com (plus).', { exact: true })).toBeVisible();
        await chat.getByRole('button', { name: 'Close', exact: true }).click();
    }
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
    await chat.getByRole('button', { name: 'Send', exact: true }).click();
    await expect(
        chat.getByText('1 red-label annotation added to the image. Edit or Undo, then Submit to save.')
    ).toBeVisible();
    expect(await page.evaluate(() => Reflect.get(window, 'codexOperationCounts'))).toEqual({ status: 1, conflicts: 0 });
});

test('clearing or closing chat preserves existing and automatically added annotations', async ({
    page,
    annotatorPage,
    network,
}) => {
    network.use(
        http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () =>
            HttpResponse.json({
                annotations: [
                    {
                        labels: [{ id: redLabel.id }],
                        shape: { type: 'rectangle', x: 400, y: 300, width: 50, height: 50 },
                    },
                ],
                user_reviewed: true,
                subset: 'training',
            })
        )
    );
    await annotatorPage.goto(project.id, 'item-1');
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    const existing = page
        .getByTestId('annotation-layer')
        .getByLabel(`label ${redLabel.name} background`, { exact: true });
    let count = 1;
    for (const action of ['Clear conversation', 'Close']) {
        await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
        await chat.getByRole('button', { name: 'Send', exact: true }).click();
        await expect(
            chat.getByText('1 red-label annotation added to the image. Edit or Undo, then Submit to save.')
        ).toBeVisible();
        count += 1;
        await expect(existing).toHaveCount(count);
        await chat.getByRole('button', { name: action, exact: true }).click();
        await expect(existing).toHaveCount(count);
    }
});

test('selects an account model in chat, sends its model ID and remembers the choice', async ({
    page,
    annotatorPage,
}) => {
    await annotatorPage.goto(project.id, 'item-1');
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    const picker = chat.getByRole('button', { name: /Model$/ });
    await expect(chat.getByText('Loading available models…')).toHaveCount(0);
    await expect(picker).toBeEnabled();
    await picker.click();
    await page.getByRole('option', { name: 'GPT-6-Astra', exact: true }).click();
    await chat.getByRole('button', { name: 'Send', exact: true }).click();
    await expect(
        chat.getByText('1 red-label annotation added to the image. Edit or Undo, then Submit to save.')
    ).toBeVisible();
    expect(await page.evaluate(() => Reflect.get(window, 'lastRequestModel'))).toBe('gpt-6-astra');
    await chat.getByRole('button', { name: 'Close', exact: true }).click();
    await page.reload();
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    await expect(picker).toContainText('GPT-6-Astra');
    await picker.click();
    await page.getByRole('option', { name: 'Account default', exact: true }).click();
    await chat.getByRole('button', { name: 'Send', exact: true }).click();
    await expect(
        chat.getByText('1 red-label annotation added to the image. Edit or Undo, then Submit to save.')
    ).toBeVisible();
    expect(await page.evaluate(() => Reflect.get(window, 'lastRequestModel'))).toBeNull();
});

test('keeps the model selector visible on a failed lookup and retries without signing out', async ({
    page,
    annotatorPage,
}) => {
    await annotatorPage.goto(project.id, 'item-1');
    await page.evaluate(() => {
        const internals = Reflect.get(window, '__TAURI_INTERNALS__');
        if (!internals) throw new Error('Missing desktop mock');
        const invoke = Reflect.get(internals, 'invoke') as (
            command: string,
            args: Record<string, unknown>
        ) => Promise<unknown>;
        let fail = true;
        Reflect.set(internals, 'invoke', (command: string, args: Record<string, unknown>) => {
            if (command === 'codex_operation' && args.operation === 'models' && fail) {
                fail = false;
                return Promise.reject('Temporary model list error');
            }
            return invoke(command, args);
        });
    });
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    await expect(chat.getByRole('status')).toContainText('Temporary model list error');
    const picker = chat.getByRole('button', { name: /Model$/ });
    await expect(picker).toBeVisible();
    await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
    await chat.getByRole('button', { name: 'Retry model list' }).click();
    await expect(chat.getByRole('button', { name: 'Retry model list' })).toHaveCount(0);
    await picker.click();
    await expect(page.getByRole('option', { name: 'GPT-5.6-Sol', exact: true })).toBeVisible();
    await page.screenshot({ path: 'test-results/chatgpt-model-selector.png' });
});

test('keeps every batch when a response adds annotations more than once', async ({ page, annotatorPage }) => {
    await annotatorPage.goto(project.id, 'item-1');
    await page.evaluate(() => {
        const internals = Reflect.get(window, '__TAURI_INTERNALS__');
        if (!internals) throw new Error('Missing desktop mock');
        const invoke = Reflect.get(internals, 'invoke') as (
            command: string,
            args: Record<string, unknown>
        ) => Promise<{ calls?: { name: string; arguments: string }[] }>;
        Reflect.set(internals, 'invoke', async (command: string, args: Record<string, unknown>) => {
            const response = await invoke(command, args);
            if (response?.calls?.[0]?.name === 'propose_annotations') {
                const call = response.calls[0];
                const payload = JSON.parse(call.arguments);
                return {
                    ...response,
                    calls: [
                        call,
                        {
                            ...call,
                            arguments: JSON.stringify({
                                ...payload,
                                annotations: [{ label_ids: ['red-label'], x: 400, y: 300, width: 50, height: 50 }],
                            }),
                        },
                    ],
                };
            }
            return response;
        });
    });
    await page.getByRole('button', { name: 'Annotate with ChatGPT', exact: true }).click();
    const chat = page.getByRole('complementary', { name: 'Annotate with ChatGPT' });
    await expect(chat.getByRole('button', { name: 'Send', exact: true })).toBeEnabled();
    await chat.getByRole('button', { name: 'Send', exact: true }).click();
    const labels = page
        .getByTestId('annotation-layer')
        .getByLabel(`label ${redLabel.name} background`, { exact: true });
    await expect(labels).toHaveCount(2);
    await annotatorPage.undoAnnotation();
    await expect(labels).toHaveCount(1);
    await annotatorPage.undoAnnotation();
    await expect(labels).toHaveCount(0);
    await annotatorPage.redoAnnotation();
    await annotatorPage.redoAnnotation();
    await expect(labels).toHaveCount(2);
});
