// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen, waitFor } from '@testing-library/react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedImage } from '../../../../../test-utils/utils';
import { ANNOTATOR_MODE } from '../../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import {
    AnnotationToolProvider,
    useAnnotationToolContext,
} from '../../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../../providers/task-chain-provider/task-chain-provider.component';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../zoom/zoom-provider.component';
import { defaultAnnotationState } from '../test-utils';
import { AnnotationActions } from './annotation-actions.component';

jest.mock('../../../providers/task-chain-provider/task-chain-provider.component', () => ({
    ...jest.requireActual('../../../providers/task-chain-provider/task-chain-provider.component'),
    useTaskChain: jest.fn(),
}));

jest.mock('../../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    ...jest.requireActual('../../../providers/region-of-interest-provider/region-of-interest-provider.component'),
    useROI: jest.fn(),
}));

jest.mock('../../../hooks/use-annotator-mode', () => ({
    useAnnotatorMode: jest.fn(() => ({
        isActiveLearningMode: true,
        currentMode: 'active-learning',
    })),
}));

describe('Annotation actions', () => {
    beforeEach(() => {
        jest.clearAllMocks();

        const roi = { x: 0, y: 0, width: 200, height: 200 };
        jest.mocked(useROI).mockReturnValue({
            roi,
            image: getMockedImage(roi),
        });
    });

    const renderAnnotationListContainer = (
        annotations: Annotation[] = defaultAnnotationState,
        isTaskChainSelectedClassification = false
    ) => {
        const annotationToolContext = fakeAnnotationToolContext({
            annotations,
        });

        jest.mocked(useAnnotationToolContext).mockImplementation(() => {
            return annotationToolContext;
        });

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs: [],
            outputs: annotations,
        }));

        return render(
            <ZoomProvider>
                <TransformZoomAnnotation>
                    <AnnotationToolProvider>
                        <AnnotationActions isTaskChainSelectedClassification={isTaskChainSelectedClassification}>
                            <p>other options</p>
                        </AnnotationActions>
                    </AnnotationToolProvider>
                </TransformZoomAnnotation>
            </ZoomProvider>
        );
    };

    const unselectedAnnotations = [
        getMockedAnnotation({ id: '1', isSelected: false }, ShapeType.Rect),
        getMockedAnnotation({ id: '2', zIndex: 1, isSelected: false }),
    ];

    it('Filter annotations is invisible with "isTaskChainSelectedClassification"', async () => {
        await renderAnnotationListContainer(unselectedAnnotations, true);

        await waitFor(() => {
            expect(screen.queryByRole('button', { name: 'Filter annotations' })).not.toBeInTheDocument();
        });
    });

    it('Filter annotations is visible when there are no annotations selected', async () => {
        await renderAnnotationListContainer(unselectedAnnotations);

        await waitFor(() => {
            expect(screen.getByRole('button', { name: 'Filter annotations' })).toBeInTheDocument();
        });
    });

    it('Filter annotations is always visible on prediction mode', async () => {
        jest.mocked(useAnnotatorMode).mockImplementationOnce(() => ({
            isActiveLearningMode: false,
            currentMode: ANNOTATOR_MODE.PREDICTION,
        }));

        await renderAnnotationListContainer(unselectedAnnotations);

        await waitFor(() => {
            expect(screen.getByRole('button', { name: 'Filter annotations' })).toBeVisible();
        });
    });
});
