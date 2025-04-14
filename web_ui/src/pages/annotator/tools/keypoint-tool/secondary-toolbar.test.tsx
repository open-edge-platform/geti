// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
