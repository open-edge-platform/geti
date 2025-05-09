// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import * as usehooks from 'usehooks-ts';
import * as uuid from 'uuid';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Rect } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { getImageData } from '../../../../shared/canvas-utils';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { getMockedUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useCopyPasteAnnotation } from './use-copy-paste-annotation.hook';

jest.mock('usehooks-ts');
jest.mock('uuid');

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        selectedTask: null,
    })),
}));

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: { x: 0, y: 0, width: 1920, height: 1080 },
    })),
}));

const mockedAddNotification = jest.fn();

jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: jest.fn(() => ({
        addNotification: mockedAddNotification,
    })),
}));

jest.mock('../../zoom/zoom-provider.component', () => ({
    ...jest.requireActual('../../zoom/zoom-provider.component'),
    useZoom: jest.fn(() => ({
        zoomState: { zoom: 1 },
    })),
}));

const mockedUser = getMockedUser();

jest.mock('../../../../core/users/hook/use-users.hook', () => ({
    ...jest.requireActual('../../../../core/users/hook/use-users.hook'),
    useUsers: () => ({
        useActiveUser: jest.fn(() => ({ data: mockedUser })),
    }),
}));

describe('useCopyPasteAnnotation', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const image = new Image();
    image.height = 1080;
    image.width = 1920;
    const mockImage = getImageData(image);

    const selectedMediaItem = getMockedImageMediaItem({});
    const mockedSetLsAnnotation = jest.fn();
    const mockedLabel = getMockedLabel({ id: '123' });
    const mockedShape: Rect = { x: 0, y: 0, width: 600, height: 400, shapeType: ShapeType.Rect };
    const mockedAnnotation = getMockedAnnotation({
        labels: [],
        shape: mockedShape,
    });

    const paste = () => userEvent.keyboard('{Control>}V');
    const copy = () => userEvent.keyboard('{Control>}C');

    const classificationTask = getMockedTask({ id: 'classification-id', domain: DOMAIN.CLASSIFICATION });

    describe('copy', () => {
        it('does not copy with empty selected annotations', async () => {
            const mockedContext = fakeAnnotationToolContext({});
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([{}, mockedSetLsAnnotation, jest.fn()]);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedContext.scene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await copy();

            expect(mockedSetLsAnnotation).not.toHaveBeenCalled();
        });

        it('should copy annotation to the localstorage properly', async () => {
            const mockedContext = fakeAnnotationToolContext({});
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([{}, mockedSetLsAnnotation, jest.fn()]);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedContext.scene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await copy();

            expect(mockedSetLsAnnotation).toHaveBeenCalledWith([mockedAnnotation]);
        });

        it('should not copy annotation in the classification task', async () => {
            const mockedContext = fakeAnnotationToolContext({});
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([{}, mockedSetLsAnnotation, jest.fn()]);

            // @ts-expect-error we care only about selected task
            jest.mocked(useTask).mockReturnValueOnce({
                selectedTask: classificationTask,
            });

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedContext.scene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await copy();

            expect(mockedSetLsAnnotation).not.toHaveBeenCalledWith([mockedAnnotation]);
        });
    });

    describe('paste', () => {
        it('should not paste annotations when there are no annotations in the localstorage', async () => {
            const mockedContext = fakeAnnotationToolContext({});
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([null, mockedSetLsAnnotation, jest.fn()]);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedContext.scene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await paste();

            await waitFor(() => {
                expect(mockedContext.scene.addAnnotations).not.toHaveBeenCalled();
            });
        });

        it('should not paste the annotation when the annotation is completely outside roi', async () => {
            const annotation = {
                ...mockedAnnotation,
                labels: [mockedLabel],
                shape: { ...mockedAnnotation.shape, shapeType: ShapeType.Rect, x: -mockedShape.width },
            } as unknown as Annotation;

            const mockedScene = fakeAnnotationToolContext({}).scene;
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([[annotation], mockedSetLsAnnotation, jest.fn()]);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedScene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).not.toHaveBeenCalled();
                expect(mockedAddNotification).toHaveBeenCalledWith({
                    message: "One or more annotations outside the region of interest haven't been pasted.",
                    type: NOTIFICATION_TYPE.INFO,
                });
            });
        });

        it('should paste the annotation when the annotation is partially outside roi', async () => {
            const annotationId = 'annotation-id';

            const annotation = {
                ...mockedAnnotation,
                id: annotationId,
                labels: [mockedLabel],
                shape: { ...mockedAnnotation.shape, shapeType: ShapeType.Rect, x: -mockedShape.width / 2 },
            } as unknown as Annotation;

            const mockedScene = fakeAnnotationToolContext({}).scene;
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([[annotation], mockedSetLsAnnotation, jest.fn()]);
            jest.mocked<() => string>(uuid.v4).mockReturnValue(annotationId);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedScene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).toHaveBeenCalledWith([
                    {
                        ...annotation,
                        isSelected: true,
                        shape: { ...annotation.shape, x: 0, width: mockedShape.width / 2 },
                    },
                ]);
            });
        });

        it('should not paste the annotation whose labels are invalid', async () => {
            const annotation = {
                ...mockedAnnotation,
                labels: [getMockedLabel({ id: '1111' })],
            } as unknown as Annotation;
            const mockedContext = fakeAnnotationToolContext({});
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([[annotation], mockedSetLsAnnotation, jest.fn()]);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedContext.scene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await paste();

            await waitFor(() => {
                expect(mockedContext.scene.addAnnotations).not.toHaveBeenCalled();
                expect(mockedAddNotification).toHaveBeenCalledWith({
                    message: 'You can only paste annotations in the same task context.',
                    type: NOTIFICATION_TYPE.INFO,
                });
            });
        });

        it('should paste annotation whose labels are empty', async () => {
            const annotationId = 'annotation-id';

            const mockedScene = fakeAnnotationToolContext({}).scene;
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([
                [mockedAnnotation],
                mockedSetLsAnnotation,
                jest.fn(),
            ]);
            jest.mocked<() => string>(uuid.v4).mockReturnValue(annotationId);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedScene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );
            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).toHaveBeenCalledWith([
                    { ...mockedAnnotation, shape: { ...mockedAnnotation.shape }, isSelected: true, id: annotationId },
                ]);
            });
        });

        it('should paste annotation with offset if paste was invoked more than once', async () => {
            const OFFSET = 10;

            const annotationsIds = ['annotation-id-1', 'annotation-id-2', 'annotation-id-3'];
            const mockedScene = fakeAnnotationToolContext({}).scene;
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([
                [mockedAnnotation],
                mockedSetLsAnnotation,
                jest.fn(),
            ]);

            jest.mocked<() => string>(uuid.v4)
                .mockReturnValueOnce(annotationsIds[0])
                .mockReturnValueOnce(annotationsIds[1])
                .mockReturnValueOnce(annotationsIds[2]);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedScene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );
            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).toHaveBeenCalledWith([
                    {
                        ...mockedAnnotation,
                        shape: { ...mockedAnnotation.shape },
                        isSelected: true,
                        id: annotationsIds[0],
                    },
                ]);
            });

            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).toHaveBeenCalledWith([
                    {
                        ...mockedAnnotation,
                        shape: { ...mockedAnnotation.shape, x: OFFSET, y: OFFSET },
                        isSelected: true,
                        id: annotationsIds[1],
                    },
                ]);
            });

            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).toHaveBeenCalledWith([
                    {
                        ...mockedAnnotation,
                        shape: { ...mockedAnnotation.shape, x: OFFSET * 2, y: OFFSET * 2 },
                        isSelected: true,
                        id: annotationsIds[2],
                    },
                ]);
            });
        });

        it('should not paste annotation in the classification task', async () => {
            const mockedScene = fakeAnnotationToolContext({}).scene;
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([
                [mockedAnnotation],
                mockedSetLsAnnotation,
                jest.fn(),
            ]);

            // @ts-expect-error we care only about selected task
            jest.mocked(useTask).mockReturnValueOnce({
                selectedTask: classificationTask,
            });

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedScene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [mockedAnnotation],
                    image: mockImage,
                    selectedMediaItem,
                })
            );

            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).not.toHaveBeenCalled();
            });
        });

        it("should paste copied prediction as user's annotation", async () => {
            const annotationId = 'annotation-id';

            const prediction = getMockedAnnotation({
                ...mockedAnnotation,
                labels: [
                    {
                        ...mockedLabel,
                        source: { userId: undefined, modelId: 'model-id', modelStorageId: 'model-storage-id' },
                        score: 1,
                    },
                ],
            });

            const mockedScene = fakeAnnotationToolContext({}).scene;
            jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([[prediction], mockedSetLsAnnotation, jest.fn()]);
            jest.mocked<() => string>(uuid.v4).mockReturnValue(annotationId);

            renderHook(() =>
                useCopyPasteAnnotation({
                    scene: mockedScene,
                    taskLabels: [mockedLabel],
                    selectedAnnotations: [prediction],
                    image: mockImage,
                    selectedMediaItem,
                })
            );
            await paste();

            await waitFor(() => {
                expect(mockedScene.addAnnotations).toHaveBeenCalledWith([
                    expect.objectContaining({
                        ...prediction,
                        shape: { ...prediction.shape },
                        labels: prediction.labels.map((label) => labelFromUser(label, mockedUser.id)),
                        isSelected: true,
                        id: annotationId,
                    }),
                ]);
            });
        });

        describe('keypoint detection', () => {
            it('multiple annotations are not allowed', async () => {
                const mockedScene = fakeAnnotationToolContext({}).scene;
                jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([[], mockedSetLsAnnotation, jest.fn()]);
                jest.mocked<() => string>(uuid.v4).mockReturnValue('annotation-id');

                renderHook(() =>
                    useCopyPasteAnnotation({
                        scene: mockedScene,
                        taskLabels: [mockedLabel],
                        selectedAnnotations: [],
                        image: mockImage,
                        selectedMediaItem,
                        hasMultipleAnnotations: true,
                    })
                );
                await paste();

                await waitFor(() => {
                    expect(mockedAddNotification).toHaveBeenCalledWith({
                        message: 'Multiple annotations are not allowed for this task.',
                        type: NOTIFICATION_TYPE.INFO,
                    });

                    expect(mockedScene.addAnnotations).not.toHaveBeenCalled();
                });
            });

            it('paste a new annotation', async () => {
                const annotationId = 'annotation-id';

                const mockedKeypointAnnotation = getMockedAnnotation({
                    id: annotationId,
                    labels: [],
                    shape: {
                        shapeType: ShapeType.Pose,
                        points: [
                            getMockedKeypointNode({ label: mockedLabel, x: 0, y: 0 }),
                            getMockedKeypointNode({ label: mockedLabel, x: 10, y: 10 }),
                            getMockedKeypointNode({ label: mockedLabel, x: 0, y: 10 }),
                        ],
                    },
                });

                const mockedScene = fakeAnnotationToolContext({}).scene;
                jest.mocked(usehooks.useLocalStorage).mockReturnValueOnce([
                    [mockedKeypointAnnotation],
                    mockedSetLsAnnotation,
                    jest.fn(),
                ]);
                jest.mocked<() => string>(uuid.v4).mockReturnValue(annotationId);

                renderHook(() =>
                    useCopyPasteAnnotation({
                        scene: mockedScene,
                        taskLabels: [mockedLabel],
                        selectedAnnotations: [],
                        image: mockImage,
                        selectedMediaItem,
                        hasMultipleAnnotations: false,
                    })
                );
                await paste();

                await waitFor(() => {
                    expect(mockedScene.addAnnotations).toHaveBeenCalledWith([
                        { ...mockedKeypointAnnotation, isSelected: true },
                    ]);
                });
            });
        });
    });
});
