// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { createInMemoryAnnotationService } from '../../../../../core/annotations/services/in-memory-annotation-service';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../../core/annotations/utils';
import { API_URLS } from '../../../../../core/services/urls';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedDatasetIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { mockedProjectContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask, mockedTaskContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationSceneProvider } from '../../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationThresholdProvider } from '../../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import {
    AnnotatorContextProps,
    useAnnotator,
} from '../../../providers/annotator-provider/annotator-provider.component';
import { useSaveAnnotations } from '../../../providers/annotator-provider/use-save-annotations.hook';
import {
    SelectedMediaItemProps,
    useSelectedMediaItem,
} from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useSubmitAnnotations } from '../../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { UseSubmitAnnotationsMutationResult } from '../../../providers/submit-annotations-provider/submit-annotations.interface';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { VideoPlayerProvider } from '../video-player-provider.component';
import { PropagateAnnotations } from './propagate-annotations.component';

const mockDatasetIdentifier = getMockedDatasetIdentifier();

jest.mock('../../../providers/annotator-provider/use-save-annotations.hook', () => ({
    ...jest.requireActual('../../../providers/annotator-provider/use-save-annotations.hook'),
    useSaveAnnotations: jest.fn(),
}));

jest.mock('../../../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../../../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

jest.mock('../../../providers/dataset-provider/dataset-provider.component', () => ({
    useDataset: jest.fn(() => ({
        isInActiveMode: false,
        activeMediaItemsQuery: {
            data: [],
        },
    })),
}));

jest.mock('../../../hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: () => mockDatasetIdentifier,
}));

jest.mock('../../../../project-details/providers/project-provider/project-provider.component', () => {
    return {
        ...jest.requireActual('../../../../project-details/providers/project-provider/project-provider.component'),
        useProject: jest.fn(() => ({
            isTaskChainProject: false,
            project: { tasks: [] },
        })),
    };
});

jest.mock('../../../providers/task-provider/task-provider.component', () => {
    return {
        ...jest.requireActual('../../../providers/task-provider/task-provider.component'),
        useTask: jest.fn(() => ({
            selectedTask: null,
        })),
    };
});

jest.mock('../../../providers/submit-annotations-provider/submit-annotations-provider.component', () => {
    return {
        ...jest.requireActual('../../../providers/submit-annotations-provider/submit-annotations-provider.component'),
        useSubmitAnnotations: jest.fn(),
    };
});

jest.mock('uuid', () => {
    const actual = jest.requireActual('uuid');
    return {
        ...actual,
        v4: jest.fn(),
    };
});

jest.mock('../../../providers/annotator-provider/annotator-provider.component', () => ({
    ...jest.requireActual('../../../providers/annotator-provider/annotator-provider.component'),
    useAnnotator: jest.fn(() => ({
        setMode: jest.fn(),
    })),
}));

describe('Propagate annotations', () => {
    const IMAGE_ROI = { x: 0, y: 0, width: 100, height: 100 };
    const selectedMediaItem = { image: { ...new Image(), ...IMAGE_ROI } };

    jest.mocked(useSelectedMediaItem).mockImplementation(
        () => ({ selectedMediaItem }) as unknown as SelectedMediaItemProps
    );
    jest.mocked(useAnnotator).mockImplementation(() => ({ setMode: jest.fn() }) as unknown as AnnotatorContextProps);

    jest.mocked(useSubmitAnnotations).mockImplementation(() => {
        const submitAnnotationsMutation = {
            mutate: async ({ callback }: { callback: () => Promise<void> }) => {
                if (callback) {
                    await callback();
                }
            },
        } as unknown as UseSubmitAnnotationsMutationResult;

        return {
            confirmSaveAnnotations: jest.fn(),
            setUnfinishedShapeCallback: jest.fn(),
            submitAnnotationsMutation,
        };
    });

    const videoFrame = getMockedVideoFrameMediaItem({});

    const src = API_URLS.MEDIA_ITEM_SRC(mockDatasetIdentifier, { ...videoFrame.identifier, frameNumber: 60 });

    const thumbnailSrc = API_URLS.MEDIA_ITEM_THUMBNAIL(mockDatasetIdentifier, {
        ...videoFrame.identifier,
        frameNumber: 60,
    });
    const videoFrames = [
        videoFrame,
        { ...videoFrame, identifier: { ...videoFrame.identifier, frameNumber: 60 }, src, thumbnailSrc },
    ];

    const labels = [labelFromUser(getMockedLabel())];
    const currentAnnotations = [getMockedAnnotation({ id: 'test-1', labels })];

    const renderPropagateAnnotations = async (annotations: Annotation[], userAnnotations: Annotation[]) => {
        const saveAnnotations = jest.fn();
        const selectVideoFrame = jest.fn();

        const annotationService = createInMemoryAnnotationService();
        annotationService.getAnnotations = jest.fn(async () => userAnnotations);

        jest.mocked(useSaveAnnotations).mockImplementation(() => saveAnnotations);

        render(
            <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                <VideoPlayerProvider selectVideoFrame={selectVideoFrame} videoFrame={videoFrames[0]}>
                    <AnnotationSceneProvider annotations={annotations} labels={[]}>
                        <PropagateAnnotations />
                    </AnnotationSceneProvider>
                </VideoPlayerProvider>
            </AnnotationThresholdProvider>,
            { services: { annotationService } }
        );

        await waitFor(() => expect(screen.getByRole('button')).not.toBeDisabled(), { timeout: 10000 });

        return { saveAnnotations };
    };

    beforeEach(() => {
        jest.mocked(useTask).mockImplementation(() => mockedTaskContextProps({ selectedTask: getMockedTask({}) }));
    });

    it('Propagates annotations to the next video frame', async () => {
        const { saveAnnotations } = await renderPropagateAnnotations(currentAnnotations, []);

        fireEvent.click(screen.getByRole('button'));

        await waitFor(() => {
            expect(saveAnnotations).toHaveBeenCalled();
        });
        expect(saveAnnotations).toHaveBeenCalledWith(currentAnnotations, videoFrames[1]);
    });

    it('Replaces the users old annotations', async () => {
        const userAnnotations = [getMockedAnnotation({ id: 'existing-annotation-1' })];
        const { saveAnnotations } = await renderPropagateAnnotations(currentAnnotations, userAnnotations);

        fireEvent.click(screen.getByRole('button'));

        fireEvent.click(await screen.findByRole('button', { name: /replace/i }));

        await waitForElementToBeRemoved(screen.getByRole('dialog'));
        expect(saveAnnotations).toHaveBeenCalledWith(currentAnnotations, videoFrames[1]);
    });

    it('Merges the users old annotations', async () => {
        const userAnnotations = [getMockedAnnotation({ id: 'existing-annotation-1' })];
        const { saveAnnotations } = await renderPropagateAnnotations(currentAnnotations, userAnnotations);

        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(await screen.findByRole('button', { name: /merge/i }));

        await waitForElementToBeRemoved(screen.getByRole('dialog'));
        expect(saveAnnotations).toHaveBeenCalledWith([...userAnnotations, ...currentAnnotations], videoFrames[1]);
    });

    it('Cancels the users old annotations', async () => {
        const userAnnotations = [getMockedAnnotation({ id: 'existing-annotation-1' })];
        const { saveAnnotations } = await renderPropagateAnnotations(currentAnnotations, userAnnotations);

        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(await screen.findByRole('button', { name: /cancel/i }));

        await waitForElementToBeRemoved(screen.getByRole('dialog'));
        expect(saveAnnotations).not.toBeCalled();
    });

    it('Is disabled when there is no next video frame', async () => {
        const PropagateAnnotationsWithEmptyVideoFrames = ({ annotations }: { annotations: Annotation[] }) => {
            const selectVideoFrame = jest.fn();
            return (
                <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                    <VideoPlayerProvider
                        selectVideoFrame={selectVideoFrame}
                        videoFrame={{
                            ...videoFrame,
                            identifier: { ...videoFrame.identifier, frameNumber: 540 },
                            src,
                            thumbnailSrc,
                        }}
                    >
                        <AnnotationSceneProvider annotations={annotations} labels={[]}>
                            <PropagateAnnotations />
                        </AnnotationSceneProvider>
                    </VideoPlayerProvider>
                </AnnotationThresholdProvider>
            );
        };

        const annotationService = createInMemoryAnnotationService();
        annotationService.getAnnotations = jest.fn(async () => []);

        await render(<PropagateAnnotationsWithEmptyVideoFrames annotations={currentAnnotations} />, {
            services: { annotationService },
        });

        expect(screen.getByRole('button')).toBeDisabled();
    });

    it('Is disabled when there are no annotations to propagate', async () => {
        render(
            <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                <VideoPlayerProvider selectVideoFrame={jest.fn()} videoFrame={videoFrames[0]}>
                    <AnnotationSceneProvider annotations={[]} labels={[]}>
                        <PropagateAnnotations />
                    </AnnotationSceneProvider>
                </VideoPlayerProvider>
            </AnnotationThresholdProvider>
        );

        expect(screen.getByRole('button')).toBeDisabled();
    });

    it('When merging annotations with duplicated ids it creates a new annotations if those annotations were changed', async () => {
        const mockedId = 'test-new-id';
        jest.mocked<() => string>(uuidv4).mockImplementation(() => mockedId);

        const oldShape = { shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 } as const;
        const userAnnotations = [
            getMockedAnnotation({ id: 'existing-annotation-1', zIndex: 1, shape: oldShape, labels }),
            getMockedAnnotation({ id: 'existing-annotation-2', zIndex: 2, labels }),
        ];

        const annotationsToBeMerged = [
            getMockedAnnotation({
                id: 'existing-annotation-1',
                zIndex: 1,
                shape: { ...oldShape, x: 10, y: 10 },
                labels,
            }),
        ];

        const expectedMergedAnnotations = [
            getMockedAnnotation({ id: 'existing-annotation-1', zIndex: 1, shape: oldShape, labels }),
            getMockedAnnotation({ id: 'existing-annotation-2', zIndex: 2, labels }),
            getMockedAnnotation({ id: mockedId, zIndex: 1, shape: { ...oldShape, x: 10, y: 10 }, labels }),
        ];
        const { saveAnnotations } = await renderPropagateAnnotations(annotationsToBeMerged, userAnnotations);

        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(await screen.findByRole('button', { name: /merge/i }));

        await waitForElementToBeRemoved(screen.getByRole('dialog'));
        expect(saveAnnotations).toHaveBeenCalledWith(expectedMergedAnnotations, videoFrames[1]);
    });

    it('ignores annotations that were not changed', async () => {
        const mockedId = 'test-new-id';
        jest.mocked<() => string>(uuidv4).mockReturnValue(mockedId);

        const oldShape = { shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 } as const;
        const userAnnotations = [
            getMockedAnnotation({ id: 'existing-annotation-1', zIndex: 1, shape: oldShape, labels }),
            getMockedAnnotation({ id: 'existing-annotation-2', zIndex: 2, labels }),
        ];

        const annotationsToBeMerged = [userAnnotations[0]];

        const expectedMergedAnnotations = [
            getMockedAnnotation({ id: 'existing-annotation-1', zIndex: 1, shape: oldShape, labels }),
            getMockedAnnotation({ id: 'existing-annotation-2', zIndex: 2, labels }),
        ];

        const { saveAnnotations } = await renderPropagateAnnotations(annotationsToBeMerged, userAnnotations);

        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(await screen.findByRole('button', { name: /merge/i }));

        await waitForElementToBeRemoved(screen.getByRole('dialog'));
        expect(saveAnnotations).toHaveBeenCalledWith(expectedMergedAnnotations, videoFrames[1]);
    });

    it('Is disabled when a task chain project task is selected', async () => {
        // Simulate a task chain project where the user has selected a task
        jest.mocked(useProject).mockImplementation(() => mockedProjectContextProps({ isTaskChainProject: true }));

        render(
            <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                <VideoPlayerProvider selectVideoFrame={jest.fn()} videoFrame={videoFrames[0]}>
                    <AnnotationSceneProvider annotations={currentAnnotations} labels={[]}>
                        <PropagateAnnotations />
                    </AnnotationSceneProvider>
                </VideoPlayerProvider>
            </AnnotationThresholdProvider>
        );

        expect(screen.getByRole('button')).toBeDisabled();
    });
});
