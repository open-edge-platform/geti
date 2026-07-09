// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { type ReactNode } from 'react';

import { waitFor } from '@testing-library/react';
import { getMockedShape } from 'mocks/mock-annotation';
import { getMockedLabel } from 'mocks/mock-labels';
import { getMockedMediaImage } from 'mocks/mock-media';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';

import type { AnnotationDTO, Label } from '../../../../api/shared-types';
import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { AnnotationActionsProvider } from '../../../../shared/annotator/annotation-actions-provider.component';
import type { AnnotatorMode } from '../../../../shared/annotator/annotator-mode';
import { renderHook } from '../../../../test-utils/render';
import { useIsSubmitDisabled } from './use-is-submit-disabled.hook';

type RenderIsSubmitDisabledParams = {
    mode?: AnnotatorMode;
    hasSubsetChanged?: boolean;
    isLoadingPredictions?: boolean;
    initialAnnotationsDTO?: AnnotationDTO[];
    initialPredictionsDTO?: AnnotationDTO[];
    labels?: Label[];
};

const renderIsSubmitDisabled = ({
    mode = 'annotation',
    hasSubsetChanged = false,
    isLoadingPredictions = false,
    initialAnnotationsDTO = [],
    initialPredictionsDTO = [],
    labels = [],
}: RenderIsSubmitDisabledParams) => {
    server.use(
        http.get('/api/projects/{project_id}', () =>
            HttpResponse.json(getMockedProject({ task: { task_type: 'detection', exclusive_labels: false, labels } }))
        )
    );

    const wrapper = ({ children }: { children: ReactNode }) => (
        <AnnotationActionsProvider
            mode={mode}
            mediaItem={getMockedMediaImage()}
            initialAnnotationsDTO={initialAnnotationsDTO}
            initialPredictionsDTO={initialPredictionsDTO}
        >
            {children}
        </AnnotationActionsProvider>
    );

    return renderHook(() => useIsSubmitDisabled({ mode, hasSubsetChanged, isLoadingPredictions }), { wrapper });
};

describe('useIsSubmitDisabled', () => {
    const label1 = getMockedLabel({ id: 'label-1', name: 'Cat', color: '#FF0000' });

    it('annotation mode: disabled when annotations and subset are both unchanged', async () => {
        const annotationsDTO: AnnotationDTO[] = [
            { labels: [{ id: label1.id }], shape: getMockedShape({ type: 'rectangle' }), confidences: null },
        ];

        const { result } = renderIsSubmitDisabled({
            mode: 'annotation',
            labels: [label1],
            initialAnnotationsDTO: annotationsDTO,
            hasSubsetChanged: false,
        });

        await waitFor(() => expect(result.current).toBe(true));
    });

    it('annotation mode: enabled when annotations are unchanged but subset changed', async () => {
        const annotationsDTO: AnnotationDTO[] = [
            { labels: [{ id: label1.id }], shape: getMockedShape({ type: 'rectangle' }), confidences: null },
        ];

        const { result } = renderIsSubmitDisabled({
            mode: 'annotation',
            labels: [label1],
            initialAnnotationsDTO: annotationsDTO,
            hasSubsetChanged: true,
        });

        await waitFor(() => expect(result.current).toBe(false));
    });

    it('prediction mode: enabled when a prediction is present', async () => {
        const predictionsDTO: AnnotationDTO[] = [
            { labels: [{ id: label1.id }], shape: getMockedShape({ type: 'rectangle' }), confidences: [0.9] },
        ];

        const { result } = renderIsSubmitDisabled({
            mode: 'prediction',
            labels: [label1],
            initialPredictionsDTO: predictionsDTO,
        });

        await waitFor(() => expect(result.current).toBe(false));
    });

    it('prediction mode: disabled while loading predictions, even with a prediction present', async () => {
        const predictionsDTO: AnnotationDTO[] = [
            { labels: [{ id: label1.id }], shape: getMockedShape({ type: 'rectangle' }), confidences: [0.9] },
        ];

        const { result } = renderIsSubmitDisabled({
            mode: 'prediction',
            labels: [label1],
            initialPredictionsDTO: predictionsDTO,
            isLoadingPredictions: true,
        });

        await waitFor(() => expect(result.current).toBe(true));
    });
});
