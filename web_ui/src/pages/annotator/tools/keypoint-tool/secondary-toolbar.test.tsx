// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useVisibleAnnotations } from '../../hooks/use-visible-annotations.hook';
import { annotatorRender } from '../../test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { KeypointStateContextProps, useKeypointState } from './keypoint-state-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

jest.mock('../../hooks/use-visible-annotations.hook', () => ({
    useVisibleAnnotations: jest.fn(() => []),
}));

jest.mock('./keypoint-state-provider.component', () => ({
    useKeypointState: jest.fn(),
}));

describe('KeypointTool', () => {
    const renderApp = async ({
        annotations = [],
        keypointState,
        annotationToolContext = fakeAnnotationToolContext(),
    }: {
        annotations?: Annotation[];
        keypointState?: Partial<KeypointStateContextProps>;
        annotationToolContext?: AnnotationToolContext;
    }) => {
        jest.mocked(useVisibleAnnotations).mockReturnValue(annotations);
        jest.mocked(useKeypointState).mockReturnValue({
            templateLabels: [],
            templatePoints: [],
            currentBoundingBox: null,
            setCurrentBoundingBox: jest.fn(),
            setCursorDirection: jest.fn(),
            ...keypointState,
        });

        return annotatorRender(
            <ZoomProvider>
                <TransformZoomAnnotation>
                    <SecondaryToolbar annotationToolContext={annotationToolContext} />
                </TransformZoomAnnotation>
            </ZoomProvider>
        );
    };

    describe('toolbar options are disabled', () => {
        it('no annotations are present', async () => {
            await renderApp({ annotations: [getMockedAnnotation({})] });

            expect(screen.getByRole('button', { name: 'delete keypoint annotation' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror X-axis' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror Y-axis' })).toBeDisabled();
        });

        it('other annotations', async () => {
            await renderApp({});

            expect(screen.getByRole('button', { name: 'delete keypoint annotation' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror X-axis' })).toBeDisabled();
            expect(screen.getByRole('button', { name: 'mirror Y-axis' })).toBeDisabled();
        });
    });

    it('enables toolbar buttons when keypoints annotations are present', async () => {
        await renderApp({ annotations: [getMockedAnnotation({}, ShapeType.Pose)] });

        expect(screen.getByRole('button', { name: 'delete keypoint annotation' })).toBeEnabled();
        expect(screen.getByRole('button', { name: 'mirror X-axis' })).toBeEnabled();
        expect(screen.getByRole('button', { name: 'mirror Y-axis' })).toBeEnabled();
    });

    it('accepts keypoint annotation with a label so it does not get flagged as invalid', async () => {
        const mockedLabel = getMockedLabel({ id: 'test-label' });
        const annotationToolContext = fakeAnnotationToolContext();

        await renderApp({
            annotationToolContext,
            annotations: [getMockedAnnotation({}, ShapeType.Pose)],
            keypointState: {
                templateLabels: [mockedLabel],
                currentBoundingBox: { x: 0, y: 0, width: 10, height: 10 },
            },
        });

        fireEvent.click(screen.getByRole('button', { name: /accept new keypoint annotation/i }));

        expect(annotationToolContext.scene.replaceAnnotations).toHaveBeenCalledWith([
            expect.objectContaining({
                labels: expect.arrayContaining([
                    expect.objectContaining({
                        id: mockedLabel.id,
                    }),
                ]),
            }),
        ]);
    });
});
