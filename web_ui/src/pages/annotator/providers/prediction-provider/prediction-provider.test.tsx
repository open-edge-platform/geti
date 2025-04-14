// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useEffect } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Rect } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromModel, labelFromUser } from '../../../../core/annotations/utils';
import { LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../core/projects/project.interface';
import { Task } from '../../../../core/projects/task.interface';
import { useUserProjectSettings } from '../../../../core/user-settings/hooks/use-project-settings.hook';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { ProjectContextProps } from '../../../project-details/providers/project-provider/project-provider.interface';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { AnnotationSceneProvider } from '../annotation-scene-provider/annotation-scene-provider.component';
import { AnnotatorContextProps, useAnnotator } from '../annotator-provider/annotator-provider.component';
import { DatasetProvider } from '../dataset-provider/dataset-provider.component';
import {
    SelectedMediaItemProps,
    SelectedMediaItemProvider,
    useSelectedMediaItem,
} from '../selected-media-item-provider/selected-media-item-provider.component';
import { TaskChainProvider } from '../task-chain-provider/task-chain-provider.component';
import { TaskProvider, useTask } from '../task-provider/task-provider.component';
import { PredictionProvider, usePrediction } from './prediction-provider.component';

jest.mock('../selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

jest.mock('../annotator-provider/annotator-provider.component', () => ({
    useAnnotator: jest.fn(() => ({
        setMode: jest.fn(),
    })),
}));

jest.mock('../../../../core/user-settings/hooks/use-project-settings.hook', () => ({
    ...jest.requireActual('../../../../core/user-settings/hooks/use-project-settings.hook'),
    useUserProjectSettings: jest.fn(() => ({
        saveConfig: jest.fn(),
        config: {},
    })),
}));

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(),
}));

jest.mock('./use-prediction-roi-query.hook', () => ({
    ...jest.requireActual('./use-prediction-roi-query.hook'),
    usePredictionsRoiQuery: jest.fn(() => ({ refetch: () => Promise.resolve() })),
}));

const mockedAddNotification = jest.fn();
jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockedAddNotification }),
}));

jest.mock('../../hooks/use-annotator-mode', () => ({
    ...jest.requireActual('../../hooks/use-annotator-mode'),
    useAnnotatorMode: jest.fn(() => ({ isActiveLearningMode: true })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ organizationId: 'organization-id', workspaceId: 'workspace_1', projectId: 'project-id' }),
}));

// This component automatically selects the given task so that we don't need to mock
// the TaskProvider's `useTask` hook
const SelectTask = ({ task }: { task: Task | null }) => {
    const { selectedTask, setSelectedTask } = useTask();

    useEffect(() => {
        if (task?.id !== selectedTask?.id) {
            setSelectedTask(task);
        }
    }, [selectedTask, setSelectedTask, task]);

    return <></>;
};

const wrapper = ({
    children,
    tasks,
    selectedTask = tasks[0],
    userAnnotations = [],
    predictionAnnotations = [],
    project,
    userScene,
    currentMode = ANNOTATOR_MODE.PREDICTION,
}: {
    children?: ReactNode;
    project: ProjectProps;
    tasks: Task[];
    selectedTask?: Task | null;
    userAnnotations: Annotation[];
    userScene?: AnnotationScene;
    predictionAnnotations: Annotation[];
    currentMode?: ANNOTATOR_MODE;
}) => {
    const labels = tasks.flatMap((task) => task.labels);
    const { scene: mockedUserScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

    jest.mocked(useAnnotatorMode).mockReturnValue({
        isActiveLearningMode: currentMode === ANNOTATOR_MODE.ACTIVE_LEARNING,
        currentMode,
    });

    // For these tests we only care that the prediction provider uses the correct project
    jest.mocked(useProject).mockImplementation(() => {
        return {
            isSingleDomainProject: (domain: DOMAIN) => project.tasks.length === 1 && project.tasks[0].domain === domain,
            project,
            isTaskChainProject: tasks.length > 1,
        } as ProjectContextProps;
    });

    return (
        <TaskProvider>
            <DatasetProvider>
                <SelectedMediaItemProvider>
                    <SelectTask task={selectedTask} />
                    <AnnotationSceneProvider annotations={predictionAnnotations} labels={labels}>
                        <TaskChainProvider tasks={tasks} selectedTask={selectedTask} defaultLabel={null}>
                            <PredictionProvider
                                settings={getMockedUserProjectSettingsObject()}
                                explanations={[]}
                                initPredictions={predictionAnnotations}
                                userAnnotationScene={userScene ?? mockedUserScene}
                            >
                                {children}
                            </PredictionProvider>
                        </TaskChainProvider>
                    </AnnotationSceneProvider>
                </SelectedMediaItemProvider>
            </DatasetProvider>
        </TaskProvider>
    );
};

const renderPredictionHook = ({
    predictionAnnotations,
    userAnnotations,
    userScene,
    currentMode,
    tasks,
    selectedTask,
    project,
}: {
    project: ProjectProps;
    tasks: Task[];
    selectedTask?: Task | null;
    userAnnotations: Annotation[];
    userScene?: AnnotationScene;
    predictionAnnotations: Annotation[];
    currentMode?: ANNOTATOR_MODE;
}) => {
    return renderHookWithProviders(usePrediction, {
        wrapper: ({ children }) =>
            wrapper({
                children,
                project,
                tasks,
                selectedTask,
                predictionAnnotations,
                userAnnotations,
                userScene,
                currentMode,
            }),
    });
};

// At the moment we have a default merging behaviour for detection, segmentation,
// and task chain tasks.
// In the future however we may want to improve this logic
const describeGeneralMergingBehaviour = (
    project: ProjectProps,
    tasks: Task[],
    selectedTask: Task | null = tasks[0]
) => {
    describe(`merging annotations (selected task = ${selectedTask?.domain ?? 'All tasks'})`, () => {
        const projectPresentation = tasks.map(({ domain }) => domain).join(' -> ');

        it(`enables merging annotations for ${projectPresentation}`, () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-1' })];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                selectedTask,
            });

            expect(result.current.enableMergingPredictionsPredicate()).toBe(true);
        });

        it(`disables merging annotations for ${projectPresentation} if there are no annotations`, () => {
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations: [],
                selectedTask,
            });

            expect(result.current.enableMergingPredictionsPredicate()).toBe(false);
        });
    });
};

describe('PredictionProvider', () => {
    const IMAGE_ROI = { x: 0, y: 0, width: 300, height: 300 };
    const selectedMediaItem = { image: { ...new Image(), ...IMAGE_ROI } };
    const rectRoiShape: Rect = { shapeType: ShapeType.Rect, ...IMAGE_ROI };

    jest.mocked(useSelectedMediaItem).mockImplementation(
        () => ({ selectedMediaItem }) as unknown as SelectedMediaItemProps
    );

    jest.mocked(useAnnotator).mockImplementation(
        () => ({ setMode: jest.fn(), selectedMediaItem }) as unknown as AnnotatorContextProps
    );

    jest.mocked(useUserProjectSettings).mockImplementation(() => {
        return getMockedUserProjectSettingsObject();
    });

    const detectionLabels = [getMockedLabel({ id: 'detection-1', group: 'detection' })];
    const segmentationLabels = [getMockedLabel({ id: 'segmentation-1', group: 'segmentation' })];
    const classificationLabels = [
        getMockedLabel({ id: 'classification-1', group: 'classification', parentLabelId: 'detection-1' }),
        getMockedLabel({ id: 'classification-2', group: 'classification', parentLabelId: 'detection-1' }),
        getMockedLabel({ id: 'classification-3', group: 'classification-group-2', parentLabelId: 'detection-1' }),
    ];

    describe('single classification task', () => {
        const tasks = [getMockedTask({ id: '1', domain: DOMAIN.CLASSIFICATION, labels: classificationLabels })];
        const project = getMockedProject({
            tasks,
            domains: tasks.map(({ domain }) => domain),
        });

        it('does NOT replace predictions from classification when there is user annotation', async () => {
            const userAnnotations = [
                getMockedAnnotation({
                    id: 'user-1',
                    labels: [
                        {
                            ...getMockedLabel({}),
                            source: { userId: 'user-email@test.com', modelId: undefined, modelStorageId: undefined },
                        },
                    ],
                }),
            ];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);
            // Since this is a classification project its annotation is automatically selected
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith([
                {
                    ...userAnnotations[0],
                },
            ]);
        });

        it('replaces predictions from classification when there is empty (global) annotation', async () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-1' })];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);
            // Since this is a classification project its annotation is automatically selected
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith([
                {
                    ...predictionAnnotations[0],
                    isSelected: true,
                },
            ]);
        });

        // NOTE: this is a hacky test, merging classification annotations is not supported as this would not make sense,
        // for our current design: a classification scene can only have 1 annotation
        it('merges predictions from classification', async () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-1' })];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });
            const predictionAnnotations = [
                getMockedAnnotation({
                    id: 'user-1',
                    labels: [labelFromModel(classificationLabels[0], 0.2, '123', '321')],
                }),
            ];

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            // Since this is a classification project its annotation is automatically selected
            const expectedAnnotations = [
                {
                    ...predictionAnnotations[0],
                    isSelected: true,
                },
            ];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('disables merging annotations for single classification tasks', () => {
            const userAnnotations = [
                getMockedAnnotation({
                    id: 'user-global-1',
                    shape: rectRoiShape,
                    labels: [labelFromUser(classificationLabels[0])],
                    isSelected: true,
                }),
            ];
            const predictionAnnotations = [
                getMockedAnnotation({
                    id: 'prediction-global-1',
                    shape: rectRoiShape,
                    labels: [labelFromUser(classificationLabels[1])],
                    isSelected: true,
                }),
            ];

            const { result } = renderPredictionHook({ project, tasks, predictionAnnotations, userAnnotations });

            expect(result.current.enableMergingPredictionsPredicate()).toBe(false);
        });
    });

    describe('single detection task', () => {
        const tasks = [getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: detectionLabels })];
        const project = getMockedProject({ tasks, domains: tasks.map(({ domain }) => domain) });

        it('replaces predictions from detection', async () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-1' })];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);

            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(predictionAnnotations);
        });

        it('merges predictions from detection', async () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-1' })];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [userAnnotations[0], predictionAnnotations[0]];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        describeGeneralMergingBehaviour(project, tasks);
    });
    //Todo update them in unification tests PR
    describe('single segmentation', () => {
        const tasks = [getMockedTask({ id: '1', domain: DOMAIN.SEGMENTATION, labels: segmentationLabels })];
        const project = getMockedProject({ tasks, domains: tasks.map(({ domain }) => domain) });
        it('replaces predictions from segmentation', async () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-1' })];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);

            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(predictionAnnotations);
        });

        it('merges predictions from segmentation', async () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-1' })];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-1' })];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [userAnnotations[0], predictionAnnotations[0]];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        describeGeneralMergingBehaviour(project, tasks);
    });

    describe('detection -> classification', () => {
        const tasks = [
            getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: detectionLabels }),
            getMockedTask({ id: '2', domain: DOMAIN.CLASSIFICATION, labels: classificationLabels }),
        ];

        const project = getMockedProject({ tasks, domains: tasks.map(({ domain }) => domain) });

        // These inputs are used by most of these tests by both the user and prediction annotations
        const inputs = [
            getMockedAnnotation({
                id: 'user-1',
                shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                labels: [labelFromUser(detectionLabels[0])],
                isSelected: true,
            }),
            getMockedAnnotation({
                id: 'user-2',
                shape: { shapeType: ShapeType.Rect, x: 100, y: 100, width: 100, height: 100 },
                labels: [labelFromUser(detectionLabels[0])],
            }),
        ];
        it('replaces annotations in "All tasks" mode', async () => {
            const userAnnotations = [
                inputs[0],
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[2])] },
            ];

            const predictionAnnotations = [
                { ...inputs[0], labels: [...inputs[0].labels, labelFromUser(classificationLabels[0])] },
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[1])] },
            ];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                tasks,
                project,
                userScene,
                userAnnotations,
                selectedTask: null,
                predictionAnnotations,
            });

            await result.current.acceptPrediction(false, () => false);

            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(predictionAnnotations);
        });

        it('replaces detection annotations', async () => {
            // Replace the single detection annotation with two detection annotations
            const userAnnotations = [inputs[0]];
            const predictionAnnotations = [inputs[0], inputs[1]];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);

            // Any outputs will have been removed
            const expectedAnnotations = predictionAnnotations;
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('replaces classification annotations inside a selected input', async () => {
            const selectedTask = tasks[1];

            const userAnnotations = [
                inputs[0],
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[2])] },
            ];

            const predictionAnnotations = [
                { ...inputs[0], labels: [...inputs[0].labels, labelFromUser(classificationLabels[0])] },
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[1])] },
            ];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                userScene,
                selectedTask,
                userAnnotations,
                predictionAnnotations,
            });

            await result.current.acceptPrediction(false, () => false);

            const expectedAnnotations = [predictionAnnotations[0], userAnnotations[1]];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('merges annotations in "All tasks" mode', async () => {
            const userAnnotations = [
                inputs[0],
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[2])] },
            ];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const predictionAnnotations = [
                { ...inputs[0], labels: [...inputs[0].labels, labelFromUser(classificationLabels[0])] },
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[1])] },
                getMockedAnnotation({
                    id: 'prediction-3',
                    shape: { shapeType: ShapeType.Rect, x: 200, y: 200, width: 100, height: 100 },
                    labels: [labelFromUser(detectionLabels[0])],
                }),
            ];

            const { result } = renderPredictionHook({
                project,
                tasks,
                userScene,
                userAnnotations,
                predictionAnnotations,
                selectedTask: null,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [
                predictionAnnotations[0],
                // Check that we include both the classification label from the user's annotation and prediction annotation
                {
                    ...inputs[1],
                    labels: [
                        ...inputs[1].labels,
                        labelFromUser(classificationLabels[2]),
                        labelFromUser(classificationLabels[1]),
                    ],
                },
                predictionAnnotations[2],
            ];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('merges detection annotations', async () => {
            const userAnnotations = [
                inputs[0],
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[2])] },
            ];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const predictionAnnotations = [
                { ...inputs[1], labels: [labelFromModel(detectionLabels[0], 0.2, '123', '321')] },
                getMockedAnnotation({
                    id: 'prediction-3',
                    shape: { shapeType: ShapeType.Rect, x: 200, y: 200, width: 100, height: 100 },
                    labels: [labelFromUser(detectionLabels[0])],
                }),
            ];

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            // NOTE: The score from the first predicted annotation does not replace the user's annotation
            const expectedAnnotations = [...userAnnotations, predictionAnnotations[1]];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('merges classification annotations inside a selected input', async () => {
            const userAnnotations = [
                inputs[0],
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[2])] },
            ];
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const predictionAnnotations = [
                { ...inputs[0], labels: [...inputs[0].labels, labelFromUser(classificationLabels[0])] },
                { ...inputs[1], labels: [...inputs[1].labels, labelFromUser(classificationLabels[1])] },
                getMockedAnnotation({
                    id: 'prediction-3',
                    shape: { shapeType: ShapeType.Rect, x: 200, y: 200, width: 100, height: 100 },
                    labels: [labelFromUser(detectionLabels[0])],
                }),
            ];

            const selectedTask = tasks[1];
            const { result } = renderPredictionHook({
                project,
                tasks,
                userScene,
                selectedTask,
                userAnnotations,
                predictionAnnotations,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [predictionAnnotations[0], userAnnotations[1]];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        describeGeneralMergingBehaviour(project, tasks, null);
        describeGeneralMergingBehaviour(project, tasks, tasks[0]);
        describeGeneralMergingBehaviour(project, tasks, tasks[1]);
    });

    describe('detection -> segmentation', () => {
        const tasks = [
            getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: detectionLabels }),
            getMockedTask({ id: '2', domain: DOMAIN.SEGMENTATION, labels: segmentationLabels }),
        ];

        const project = getMockedProject({ tasks, domains: tasks.map(({ domain }) => domain) });
        // These inputs are used by most of these tests by both the user and prediction annotations
        const inputs = [
            getMockedAnnotation({
                id: 'user-1',
                shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                labels: [labelFromUser(detectionLabels[0])],
                isSelected: true,
            }),
            getMockedAnnotation({
                id: 'user-2',
                shape: { shapeType: ShapeType.Rect, x: 100, y: 100, width: 100, height: 100 },
                labels: [labelFromUser(detectionLabels[0])],
            }),
        ];
        const userAnnotations = [
            ...inputs,
            getMockedAnnotation({
                id: 'circle-user-1-1',
                shape: { shapeType: ShapeType.Circle, x: 50, y: 50, r: 10 },
                labels: [labelFromUser(segmentationLabels[0])],
            }),
            getMockedAnnotation({
                id: 'circle-user-1-2',
                shape: { shapeType: ShapeType.Circle, x: 20, y: 20, r: 10 },
                labels: [labelFromUser(segmentationLabels[0])],
            }),

            // A segmentation annotation outside of the selected detection annotation
            getMockedAnnotation({
                id: 'circle-user-2-1',
                shape: { shapeType: ShapeType.Circle, x: 120, y: 120, r: 10 },
                labels: [labelFromUser(segmentationLabels[0])],
            }),
        ];

        const predictedDetectionAnnotations = [
            ...inputs,
            getMockedAnnotation({
                id: 'user-3',
                shape: { shapeType: ShapeType.Rect, x: 200, y: 200, width: 100, height: 100 },
                labels: [labelFromUser(detectionLabels[0])],
            }),
        ];
        const predictedSegmentationInputsSelectedInput = [
            getMockedAnnotation({
                id: 'prediction-1-user-1-1',
                shape: { shapeType: ShapeType.Circle, x: 20, y: 20, r: 10 },
                labels: [labelFromUser(segmentationLabels[0])],
            }),
        ];
        const predictionAnnotations = [
            ...predictedDetectionAnnotations,
            ...predictedSegmentationInputsSelectedInput,
            getMockedAnnotation({
                id: 'prediction-1-user-2-1',
                shape: { shapeType: ShapeType.Circle, x: 120, y: 120, r: 10 },
                labels: [labelFromUser(segmentationLabels[0])],
            }),
        ];
        it('replaces annotations in "All tasks" mode', async () => {
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                userScene,
                userAnnotations,
                predictionAnnotations,
                selectedTask: null,
            });

            await result.current.acceptPrediction(false, () => false);

            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(predictionAnnotations);
        });

        it('replaces detection annotations', async () => {
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);

            // Any outputs will have been removed
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(predictedDetectionAnnotations);
        });

        // TODO: this contains ambiguity?
        it('replaces segmentation annotations inside a selected input', async () => {
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const selectedTask = tasks[1];
            const { result } = renderPredictionHook({
                project,
                tasks,
                selectedTask,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);

            const expectedAnnotations = [
                ...inputs,
                userAnnotations[userAnnotations.length - 1],
                ...predictedSegmentationInputsSelectedInput,
            ];

            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        // NOTE: later on we will refactor inputs of the annotator so that the user annotation
        // and prediction scene always have the same input
        it('replaces segmentation annotations if the input is a predicted annotation', async () => {
            const userAnnotationsWithoutPredictionInput = [
                inputs[1],
                getMockedAnnotation({
                    id: 'circle-user-2-1',
                    shape: { shapeType: ShapeType.Circle, x: 120, y: 120, r: 10 },
                    labels: [labelFromUser(segmentationLabels[0])],
                }),
            ];

            const predictionAnnotationWithNewInput = [
                inputs[0],
                getMockedAnnotation({
                    id: 'prediction-1-user-1-1',
                    shape: { shapeType: ShapeType.Circle, x: 20, y: 20, r: 10 },
                    labels: [labelFromUser(segmentationLabels[0])],
                }),
            ];

            const { scene: userScene } = fakeAnnotationToolContext({
                annotations: userAnnotationsWithoutPredictionInput,
            });
            const selectedTask = tasks[1];
            const { result } = renderPredictionHook({
                project,
                tasks,
                selectedTask,
                predictionAnnotations: predictionAnnotationWithNewInput,
                userAnnotations: userAnnotationsWithoutPredictionInput,
                userScene,
            });

            await result.current.acceptPrediction(false, () => false);

            const expectedAnnotations = [
                ...userAnnotationsWithoutPredictionInput,
                predictionAnnotationWithNewInput[0],
                predictionAnnotationWithNewInput[1],
            ];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('merges annotations in "All tasks" mode', async () => {
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                tasks,
                project,
                userScene,
                userAnnotations,
                predictionAnnotations,
                selectedTask: null,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [
                ...userAnnotations,
                predictionAnnotations[2],
                predictedSegmentationInputsSelectedInput[0],
                predictionAnnotations[predictionAnnotations.length - 1],
            ];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('merges detection annotations', async () => {
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const { result } = renderPredictionHook({
                project,
                tasks,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            // Any outputs will have been removed
            const expectedAnnotations = [
                ...userAnnotations,
                predictedDetectionAnnotations[predictedDetectionAnnotations.length - 1],
            ];

            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('merges segmentation annotations inside a selected input', async () => {
            const { scene: userScene } = fakeAnnotationToolContext({ annotations: userAnnotations });

            const selectedTask = tasks[1];
            const { result } = renderPredictionHook({
                project,
                tasks,
                selectedTask,
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [...userAnnotations, ...predictedSegmentationInputsSelectedInput];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        // NOTE: later on we will refactor inputs of the annotator so that the user annotation
        // and prediction scene always have the same input
        it('merges segmentation annotations if the input is a predicted annotation', async () => {
            const userAnnotationsWithoutPredictionInput = [
                inputs[1],
                getMockedAnnotation({
                    id: 'circle-user-2-1',
                    shape: { shapeType: ShapeType.Circle, x: 120, y: 120, r: 10 },
                    labels: [labelFromUser(segmentationLabels[0])],
                }),
            ];

            const predictionAnnotationWithNewInput = [
                inputs[0],
                getMockedAnnotation({
                    id: 'prediction-1-user-1-1',
                    shape: { shapeType: ShapeType.Circle, x: 20, y: 20, r: 10 },
                    labels: [labelFromUser(segmentationLabels[0])],
                }),
            ];
            const { scene: userScene } = fakeAnnotationToolContext({
                annotations: userAnnotationsWithoutPredictionInput,
            });

            const selectedTask = tasks[1];
            const { result } = renderPredictionHook({
                project,
                tasks,
                selectedTask,
                predictionAnnotations: predictionAnnotationWithNewInput,
                userAnnotations: userAnnotationsWithoutPredictionInput,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [
                ...userAnnotationsWithoutPredictionInput,
                predictionAnnotationWithNewInput[0],
                predictionAnnotationWithNewInput[1],
            ];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });
        describeGeneralMergingBehaviour(project, tasks, null);
        describeGeneralMergingBehaviour(project, tasks, tasks[0]);
        describeGeneralMergingBehaviour(project, tasks, tasks[1]);
    });

    describe('anomaly detection', () => {
        const anomalyLabels = [
            getMockedLabel({
                id: 'normal',
                name: 'Normal',
                behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.EXCLUSIVE,
            }),
            getMockedLabel({
                id: 'anomalous',
                name: 'Anomalous',
                behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.ANOMALOUS,
            }),
        ];
        const [normalLabel, anomalousLabel] = anomalyLabels;

        const tasks = [getMockedTask({ id: '1', domain: DOMAIN.ANOMALY_DETECTION, labels: anomalyLabels })];

        const project = getMockedProject({ tasks });

        it('replaces global annotations when merging', async () => {
            const userAnnotations = [
                getMockedAnnotation({
                    id: 'user-global-1',
                    shape: rectRoiShape,
                    labels: [labelFromUser(normalLabel)],
                    isSelected: true,
                }),
            ];
            const { scene: userScene } = fakeAnnotationToolContext({
                annotations: userAnnotations,
            });

            const predictionAnnotations = [
                getMockedAnnotation({
                    id: 'prediction-global-1',
                    shape: rectRoiShape,
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
                getMockedAnnotation({
                    id: 'prediction-local-1',
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
            ];

            const { result } = renderPredictionHook({
                project,
                tasks,
                selectedTask: tasks[0],
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = predictionAnnotations;
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it('merges local annotations, but keeps only 1 global annotation', async () => {
            const userAnnotations = [
                getMockedAnnotation({
                    id: 'user-global-1',
                    shape: rectRoiShape,
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
                getMockedAnnotation({
                    id: 'user-local-1',
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
            ];
            const { scene: userScene } = fakeAnnotationToolContext({
                annotations: userAnnotations,
            });

            const predictionAnnotations = [
                getMockedAnnotation({
                    id: 'prediction-global-1',
                    shape: rectRoiShape,
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
                getMockedAnnotation({
                    id: 'prediction-local-1',
                    shape: { shapeType: ShapeType.Rect, x: 20, y: 20, width: 10, height: 10 },
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
            ];

            const { result } = renderPredictionHook({
                project,
                tasks,
                selectedTask: tasks[0],
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [userAnnotations[1], ...predictionAnnotations];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        it("keeps the user's global annotation if merged with no other global annotation ", async () => {
            const userAnnotations = [
                getMockedAnnotation({
                    id: 'user-global-1',
                    shape: rectRoiShape,
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
                getMockedAnnotation({
                    id: 'user-local-1',
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
            ];
            const { scene: userScene } = fakeAnnotationToolContext({
                annotations: userAnnotations,
            });
            const predictionAnnotations = [
                getMockedAnnotation({
                    id: 'prediction-local-1',
                    shape: { shapeType: ShapeType.Rect, x: 20, y: 20, width: 10, height: 10 },
                    labels: [labelFromUser(anomalousLabel)],
                    isSelected: true,
                }),
            ];

            const { result } = renderPredictionHook({
                project,
                tasks,
                selectedTask: tasks[0],
                predictionAnnotations,
                userAnnotations,
                userScene,
            });

            await result.current.acceptPrediction(true, () => false);

            const expectedAnnotations = [...userAnnotations, ...predictionAnnotations];
            expect(userScene.replaceAnnotations).toHaveBeenCalledWith(expectedAnnotations);
        });

        describe('merging predictions', () => {
            it('disables merging predictions if the user does not have any annotations', () => {
                const userAnnotations: Annotation[] = [];
                const predictionAnnotations = [
                    getMockedAnnotation({
                        id: 'prediction-global-1',
                        shape: rectRoiShape,
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                ];

                const { result } = renderPredictionHook({ project, tasks, predictionAnnotations, userAnnotations });

                expect(result.current.enableMergingPredictionsPredicate()).toBe(false);
            });

            it('disables merging predictions if the user only has a global annotation', () => {
                const userAnnotations = [
                    getMockedAnnotation({
                        id: 'user-global-1',
                        shape: rectRoiShape,
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                ];
                const predictionAnnotations = [
                    getMockedAnnotation({
                        id: 'prediction-global-1',
                        shape: rectRoiShape,
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                ];

                const { result } = renderPredictionHook({ project, tasks, predictionAnnotations, userAnnotations });

                expect(result.current.enableMergingPredictionsPredicate()).toBe(false);
            });

            it("disables merging predictions if the predicted global annotation conflicts with the user's global annotation", () => {
                const userAnnotations = [
                    getMockedAnnotation({
                        id: 'user-global-1',
                        shape: rectRoiShape,
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                    getMockedAnnotation({
                        id: 'user-local-1',
                        shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                ];
                const predictionAnnotations = [
                    getMockedAnnotation({
                        id: 'prediction-global-1',
                        shape: rectRoiShape,
                        labels: [labelFromUser(normalLabel)],
                        isSelected: true,
                    }),
                ];

                const { result } = renderPredictionHook({ project, tasks, predictionAnnotations, userAnnotations });

                expect(result.current.enableMergingPredictionsPredicate()).toBe(false);
            });

            it("enables merging predictions if the prediction annotations contain local anomalous annotations not in the user's annotations", () => {
                const userAnnotations = [
                    getMockedAnnotation({
                        id: 'user-global-1',
                        shape: rectRoiShape,
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                    getMockedAnnotation({
                        id: 'user-local-1',
                        shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                ];
                const predictionAnnotations = [
                    getMockedAnnotation({
                        id: 'prediction-global-1',
                        shape: rectRoiShape,
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                    getMockedAnnotation({
                        id: 'prediction-local-1',
                        shape: { shapeType: ShapeType.Rect, x: 30, y: 30, width: 10, height: 10 },
                        labels: [labelFromUser(anomalousLabel)],
                        isSelected: true,
                    }),
                ];

                const { result } = renderPredictionHook({ project, tasks, predictionAnnotations, userAnnotations });

                expect(result.current.enableMergingPredictionsPredicate()).toBe(true);
            });
        });
    });

    describe('keypoint detection', () => {
        const tasks = [getMockedTask({ id: '1', domain: DOMAIN.KEYPOINT_DETECTION, labels: segmentationLabels })];

        const project = getMockedProject({ tasks, domains: tasks.map(({ domain }) => domain) });

        it('disables merging annotations', () => {
            const userAnnotations = [getMockedAnnotation({ id: 'user-global-1' })];
            const predictionAnnotations = [getMockedAnnotation({ id: 'prediction-global-1' })];

            const { result } = renderPredictionHook({ project, tasks, predictionAnnotations, userAnnotations });

            expect(result.current.enableMergingPredictionsPredicate()).toBe(false);
        });
    });
});
