// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, within } from '@testing-library/react';
import { FocusScope } from 'react-aria';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../../core/annotations/utils';
import { LABEL_BEHAVIOUR } from '../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels as mockedLabels } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { getMockedImage } from '../../../../../test-utils/utils';
import {
    AnnotationToolProvider,
    useAnnotationToolContext,
} from '../../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../../providers/task-chain-provider/task-chain-provider.component';
import { useSelectedTask } from '../../../providers/task-provider/use-selected-task.hook';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../zoom/zoom-provider.component';
import { defaultAnnotationState } from '../test-utils';
import { AnnotationListContainer } from './annotation-list-container.component';

jest.mock('../../../providers/task-provider/use-selected-task.hook', () => ({
    ...jest.requireActual('../../../providers/task-chain-provider/task-chain-provider.component'),
    useSelectedTask: jest.fn(),
}));

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
    useROI: jest.fn(() => ({
        roi: { x: 0, y: 0, height: 100, width: 100 },
    })),
}));

const mockedProjectService = createInMemoryProjectService();
const [detectionLabel, ...classificationLabels] = mockedLabels;
const detectionClassificationTasks = [
    getMockedTask({
        id: 'detection',
        domain: DOMAIN.DETECTION,
        labels: [detectionLabel],
    }),
    getMockedTask({
        id: 'classification',
        domain: DOMAIN.CLASSIFICATION,
        labels: classificationLabels,
    }),
];

describe('Annotation list container', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    afterAll(() => {
        jest.clearAllTimers();
    });

    const replaceAnnotations = jest.fn();

    const renderAnnotationListContainer = async (
        annotations: Annotation[] = defaultAnnotationState,
        asDetectionClassification = false,
        projectService = mockedProjectService
    ) => {
        jest.mocked(useAnnotationToolContext).mockImplementation(() => fakeAnnotationToolContext({}));

        if (asDetectionClassification) {
            jest.mocked(useTaskChain).mockImplementation(() => ({
                inputs: annotations.map((annotation) => ({ ...annotation, outputs: [annotation] })),
                outputs: annotations,
            }));
        } else {
            jest.mocked(useTaskChain).mockImplementation(() => ({
                inputs: [],
                outputs: annotations,
            }));
        }

        return render(
            <FocusScope>
                <ZoomProvider>
                    <TransformZoomAnnotation>
                        <AnnotationToolProvider>
                            <AnnotationListContainer />
                        </AnnotationToolProvider>
                    </TransformZoomAnnotation>
                </ZoomProvider>
            </FocusScope>,
            { services: { projectService } }
        );
    };

    it('classification project does not have annotation actions', async () => {
        const [, classificationTask] = detectionClassificationTasks;
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => getMockedProject({ tasks: detectionClassificationTasks });
        jest.mocked(useSelectedTask).mockReturnValue([classificationTask, jest.fn()]);
        await renderAnnotationListContainer(undefined, true, projectService);

        expect(screen.queryByTestId('thumbnail grid annotation actions')).not.toBeInTheDocument();
    });

    it('render list of annotations', async () => {
        const [, classificationTask] = detectionClassificationTasks;
        jest.mocked(useSelectedTask).mockReturnValue([classificationTask, jest.fn()]);

        await renderAnnotationListContainer();

        const firstAnnotation = await screen.findByText(/dog/);
        const secondAnnotation = await screen.findByText(/parrot/);

        expect(firstAnnotation).toBeInTheDocument();
        expect(secondAnnotation).toBeInTheDocument();
        expect(replaceAnnotations).not.toHaveBeenCalled();
    });

    it('does not show global annotations in an anomaly project', async () => {
        const roi = { x: 0, y: 0, width: 200, height: 200 };
        const EMPTY_SHAPE = { shapeType: ShapeType.Rect as const, ...roi };

        const normalLabel = getMockedLabel({
            id: 'normal-label-id',
            name: 'Normal',
            behaviour: LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL,
        });

        const anomalousLabel = getMockedLabel({
            id: 'anomalous-label-id',
            name: 'Anomalous',
            behaviour: LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.ANOMALOUS,
        });

        const tasks = [
            getMockedTask({
                id: 'anomaly-segmentation',
                domain: DOMAIN.ANOMALY_SEGMENTATION,
                labels: [normalLabel, anomalousLabel],
            }),
        ];

        const annotations = [
            getMockedAnnotation(
                { id: '1', zIndex: 0, shape: EMPTY_SHAPE, labels: [labelFromUser(anomalousLabel)] },
                ShapeType.Rect
            ),
            getMockedAnnotation({ id: '2', zIndex: 1, labels: [labelFromUser(anomalousLabel)] }, ShapeType.Rect),
        ];

        const selectedTask = tasks[0];
        const annotationToolContext = fakeAnnotationToolContext({
            tasks,
            selectedTask,
            annotations,
        });

        jest.mocked(useROI).mockReturnValue({
            roi,
            image: getMockedImage(roi),
        });

        jest.mocked(useAnnotationToolContext).mockImplementation(() => {
            return annotationToolContext;
        });

        jest.mocked(useSelectedTask).mockReturnValue([selectedTask, jest.fn()]);

        await renderAnnotationListContainer(annotations);

        // Each annotation list item can have other list items per label, so we try to filter based on
        // it's aria label
        expect(
            within(screen.getByRole('listbox', { name: 'Annotations list' })).getAllByRole('listitem', {
                name: /Annotation with id/i,
            })
        ).toHaveLength(1);
    });

    it('Shows all output annotations of a detection -> classification task when classification is selected', async () => {
        const [, classificationTask] = detectionClassificationTasks;
        jest.mocked(useSelectedTask).mockReturnValue([classificationTask, jest.fn()]);

        const EMPTY_SHAPE = { shapeType: ShapeType.Rect as const, x: 0, y: 0, width: 200, height: 200 };

        const annotations = [
            getMockedAnnotation({
                id: '1',
                zIndex: 0,
                shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 100, height: 100 },
                labels: [labelFromUser(detectionLabel), labelFromUser(classificationLabels[0])],
            }),
            getMockedAnnotation({
                id: '2',
                zIndex: 1,
                shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 100, height: 100 },
                labels: [labelFromUser(detectionLabel), labelFromUser(classificationLabels[1])],
                isSelected: true,
            }),
            getMockedAnnotation({
                id: '3',
                zIndex: 0,
                shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 100, height: 100 },
                labels: [
                    labelFromUser(detectionLabel),
                    labelFromUser(classificationLabels[0]),
                    labelFromUser(classificationLabels[2]),
                ],
            }),
        ];

        const annotationToolContext = fakeAnnotationToolContext({
            tasks: detectionClassificationTasks,
            selectedTask: detectionClassificationTasks[1],
            annotations,
            roi: EMPTY_SHAPE,
        });

        jest.mocked(useAnnotationToolContext).mockImplementation(() => {
            return annotationToolContext;
        });

        await renderAnnotationListContainer(annotations, true);

        // Each annotation list item can have other list items per label, so we try to filter based on
        // it's aria label
        expect(
            within(screen.getByRole('listbox', { name: 'Annotations list' })).getAllByRole('listitem', {
                name: /Annotation with id/i,
            })
        ).toHaveLength(3);
    });
});
