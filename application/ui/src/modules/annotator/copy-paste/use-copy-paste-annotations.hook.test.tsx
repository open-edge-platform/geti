// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ReactNode } from 'react';

import type { AnnotationDTO, Label, TaskType } from '@/api/types';
import { useSetZoom, ZoomProvider } from '@/components/zoom/zoom.provider';
import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getProjectQueryOptions } from 'hooks/api/project.hook';
import { getMockedShape } from 'mocks/mock-annotation';
import { getMockedLabel } from 'mocks/mock-labels';
import { getMockedMediaImage } from 'mocks/mock-media';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { createQueryClient } from '../../../query-client/query-client';
import { useUndoRedo } from '../../../shared/undo-redo/undo-redo-provider.component';
import {
    AnnotationDocumentProvider,
    useAnnotationCommands,
    useAnnotations,
} from '../annotation-document-provider.component';
import type { AnnotatorMode } from '../annotator-mode';
import { SelectAnnotationProvider, useSelectedAnnotations } from '../select-annotation-provider.component';
import { SelectedMediaItemProvider, useSelectedMediaItem } from '../selected-media-item-provider.component';
import { AnnotationsClipboardProvider } from './annotations-clipboard-provider.component';
import { useCopyPasteAnnotations } from './use-copy-paste-annotations.hook';

const STEP = 10;
const IMAGE_SIZE = 1000;
const initialAnnotationsDTO: AnnotationDTO[] = [
    { labels: [{ id: 'label-1' }], shape: getMockedShape({ type: 'rectangle', x: 10, y: 20, width: 100, height: 50 }) },
];

const PROJECT_ID = '123';
const LABEL = getMockedLabel({ id: 'label-1' });
const getMedia = (id: string) => getMockedMediaImage({ id, width: IMAGE_SIZE, height: IMAGE_SIZE });

const getProject = (labels: Label[] = [LABEL], taskType: TaskType = 'detection') =>
    getMockedProject({ id: PROJECT_ID, task: { exclusive_labels: false, labels, task_type: taskType } });

const renderCopyPaste = async () => {
    let mode: AnnotatorMode = 'annotation';
    const queryClient = createQueryClient();

    const wrapper = ({ children }: { children: ReactNode }) => (
        <ZoomProvider>
            <SelectedMediaItemProvider mediaItem={getMedia('item-1')}>
                <AnnotationsClipboardProvider>
                    <AnnotationDocumentProvider
                        mode={mode}
                        initialAnnotationsDTO={initialAnnotationsDTO}
                        initialPredictionsDTO={initialAnnotationsDTO}
                    >
                        <SelectAnnotationProvider>
                            <input aria-label='text field' />
                            {children}
                        </SelectAnnotationProvider>
                    </AnnotationDocumentProvider>
                </AnnotationsClipboardProvider>
            </SelectedMediaItemProvider>
        </ZoomProvider>
    );

    const hook = renderHook(
        () => {
            useCopyPasteAnnotations();

            return {
                ...useAnnotations(),
                ...useAnnotationCommands(),
                ...useSelectedAnnotations(),
                ...useSelectedMediaItem(),
                ...useSetZoom(),
                undoRedo: useUndoRedo(),
            };
        },
        { wrapper, queryClient, route: `/projects/${PROJECT_ID}`, path: '/projects/:projectId' }
    );

    // The project is fetched with Suspense, so the hook has no result until it has loaded.
    await waitFor(() => expect(hook.result.current).not.toBeNull());

    const switchMode = (newMode: AnnotatorMode) => {
        mode = newMode;
        hook.rerender();
    };

    return { ...hook, queryClient, switchMode };
};

type RenderedCopyPaste = Awaited<ReturnType<typeof renderCopyPaste>>;

const selectAll = (result: RenderedCopyPaste['result']) =>
    act(() => result.current.setSelectedAnnotations(new Set(result.current.annotations.map(({ id }) => id))));

const getRectangleXs = (result: RenderedCopyPaste['result']) =>
    result.current.annotations.map(({ shape }) => (shape.type === 'rectangle' ? shape.x : NaN));

const user = userEvent.setup();
const copy = () => user.keyboard('{Control>}c{/Control}');
const paste = () => user.keyboard('{Control>}v{/Control}');

describe('useCopyPasteAnnotations', () => {
    const serveProject = (project = getProject()) =>
        server.use(http.get('/api/projects/{project_id}', () => HttpResponse.json(project)));

    beforeEach(() => serveProject());

    it('copies the selection with an info toast and pastes cascading copies on the same media', async () => {
        const { result } = await renderCopyPaste();
        selectAll(result);

        await copy();
        expect(await screen.findByLabelText('toast')).toHaveTextContent('1 annotation copied');

        await paste();
        await paste();
        await paste();

        expect(getRectangleXs(result)).toEqual([10, 10 + STEP, 10 + 2 * STEP, 10 + 3 * STEP]);
        expect(result.current.selectedAnnotations.size).toBe(1);
        expect(screen.getAllByLabelText('toast')).toHaveLength(1);
    });

    it('lowers the cascade after undo and raises it after redo', async () => {
        const { result } = await renderCopyPaste();
        selectAll(result);
        await copy();
        await paste();
        await paste();
        await paste();

        act(() => result.current.undoRedo.undo());
        await paste();
        expect(getRectangleXs(result).at(-1)).toBe(10 + 3 * STEP);

        act(() => result.current.undoRedo.undo());
        act(() => result.current.undoRedo.redo());
        await paste();
        expect(getRectangleXs(result).at(-1)).toBe(10 + 4 * STEP);
    });

    it('pastes at the original position first, then cascades, on a different media', async () => {
        const { result } = await renderCopyPaste();
        selectAll(result);
        await copy();

        act(() => result.current.setMediaItem(getMedia('item-2')));

        await paste();
        await paste();

        expect(getRectangleXs(result).slice(-2)).toEqual([10, 10 + STEP]);
    });

    it('scales the cascade step by the zoom', async () => {
        const { result } = await renderCopyPaste();
        const zoomScale = 2;
        act(() => result.current.setZoom((zoom) => ({ ...zoom, scale: zoomScale })));
        selectAll(result);
        await copy();
        await paste();

        expect(getRectangleXs(result).at(-1)).toBe(10 + STEP / zoomScale);
    });

    it('moves each rectangle and polygon toward the image center without clipping them', async () => {
        const { result } = await renderCopyPaste();
        act(() => {
            result.current.addLabeledAnnotations([
                {
                    shape: { type: 'rectangle', x: 900, y: 0, width: 100, height: 50 },
                    labels: [{ id: 'label-1' }],
                },
                {
                    shape: {
                        type: 'polygon',
                        points: [
                            { x: 900, y: 900 },
                            { x: 1000, y: 900 },
                            { x: 1000, y: 1000 },
                        ],
                    },
                    labels: [{ id: 'label-1' }],
                },
            ]);
        });
        selectAll(result);
        await copy();
        await paste();

        expect(result.current.annotations[3].shape).toMatchObject({
            type: 'rectangle',
            x: 20,
            y: 30,
            width: 100,
            height: 50,
        });
        expect(result.current.annotations[4].shape).toEqual({
            type: 'rectangle',
            x: 890,
            y: 10,
            width: 100,
            height: 50,
        });
        expect(result.current.annotations[5].shape).toEqual({
            type: 'polygon',
            points: [
                { x: 890, y: 890 },
                { x: 990, y: 890 },
                { x: 990, y: 990 },
            ],
        });
    });

    it('pastes the snapshot taken at copy time', async () => {
        const { result } = await renderCopyPaste();
        selectAll(result);
        await copy();

        const [source] = result.current.annotations;
        act(() =>
            result.current.updateAnnotations([{ ...source, shape: getMockedShape({ type: 'rectangle', x: 500 }) }])
        );
        act(() => result.current.deleteAnnotations([source.id]));
        await paste();

        expect(getRectangleXs(result)).toEqual([10 + STEP]);
    });

    it('skips annotations whose label was deleted and shows a warning', async () => {
        const { result, queryClient } = await renderCopyPaste();
        selectAll(result);
        await copy();

        act(() => {
            queryClient.setQueryData(getProjectQueryOptions(PROJECT_ID).queryKey, getProject([]));
        });
        await paste();

        expect(result.current.annotations).toHaveLength(1);
        expect(await screen.findByText('0 pasted, 1 skipped: 1 label no longer exists')).toBeInTheDocument();
    });

    it('does nothing for an empty selection, a full image selection or an empty clipboard', async () => {
        const { result } = await renderCopyPaste();

        await copy();
        await paste();

        act(() => result.current.addAnnotationWithEmptyLabel(getMockedLabel({ id: 'empty' })));
        selectAll(result);
        await copy();
        await paste();

        expect(result.current.annotations).toHaveLength(1);
        expect(screen.queryByLabelText('toast')).not.toBeInTheDocument();
    });

    it('does not copy or paste in prediction mode', async () => {
        const { result, switchMode } = await renderCopyPaste();
        selectAll(result);
        await copy();

        switchMode('prediction');
        await paste();
        await copy();
        switchMode('annotation');

        expect(result.current.annotations).toHaveLength(1);
        expect(screen.getAllByLabelText('toast')).toHaveLength(1);
    });

    it('does not copy or paste in classification projects', async () => {
        serveProject(getProject([LABEL], 'classification'));
        const { result } = await renderCopyPaste();
        selectAll(result);

        await copy();
        await paste();

        expect(result.current.annotations).toHaveLength(1);
        expect(screen.queryByLabelText('toast')).not.toBeInTheDocument();
    });

    it('does not paste while focus is in a text field', async () => {
        const { result } = await renderCopyPaste();
        selectAll(result);
        await copy();

        await user.click(document.querySelector('input') as HTMLInputElement);
        await paste();

        expect(result.current.annotations).toHaveLength(1);
    });
});
