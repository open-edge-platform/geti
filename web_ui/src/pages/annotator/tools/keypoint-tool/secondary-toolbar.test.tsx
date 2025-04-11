// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { useVisibleAnnotations } from '../../hooks/use-visible-annotations.hook';
import { annotatorRender } from '../../test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { KeypointStateProvider } from './keypoint-state-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

jest.mock('../../hooks/use-visible-annotations.hook', () => ({
    useVisibleAnnotations: jest.fn(() => []),
}));

describe('KeypointTool', () => {
    const renderApp = async (annotations: Annotation[] = []) => {
        jest.mocked(useVisibleAnnotations).mockReturnValue(annotations);

        return annotatorRender(
            <ZoomProvider>
                <TransformZoomAnnotation>
                    <KeypointStateProvider>
                        <SecondaryToolbar annotationToolContext={fakeAnnotationToolContext()} />
                    </KeypointStateProvider>
                </TransformZoomAnnotation>
            </ZoomProvider>
        );
    };

    describe('toolbar options are disabled', () => {
        it('no annotations are present', async () => {
            await renderApp([getMockedAnnotation({})]);

            expect(screen.getByRole('button', { name: 'delete keypoint annotation' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror X-axis' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror Y-axis' })).toBeDisabled();
        });

        it('other annotations', async () => {
            await renderApp();

            expect(screen.getByRole('button', { name: 'delete keypoint annotation' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror X-axis' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror Y-axis' })).toBeDisabled();
        });
    });

    it('enables toolbar buttons when keypoints annotations are present', async () => {
        await renderApp([getMockedAnnotation({}, ShapeType.Pose)]);

        expect(screen.getByRole('button', { name: 'delete keypoint annotation' })).toBeEnabled();
        expect(screen.getByRole('button', { name: 'mirror X-axis' })).toBeEnabled();
        expect(screen.getByRole('button', { name: 'mirror Y-axis' })).toBeEnabled();
    });
});
