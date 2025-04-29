// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { useSearchParams } from 'react-router-dom';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { labels as mockedLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import {
    AnnotationSceneProvider,
    useAnnotationScene,
} from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { DefaultSelectedMediaItemProvider } from '../../providers/selected-media-item-provider/default-selected-media-item-provider.component';
import { TaskChainProvider } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskContextProps, TaskProvider } from '../../providers/task-provider/task-provider.component';
import { useSelectingState } from './selecting-state-provider.component';
import { SelectingTool } from './selecting-tool.component';
import { SelectingToolType } from './selecting-tool.enums';

const mockROI = { x: 0, y: 0, height: 100, width: 100 };
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useSearchParams: jest.fn(),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('./selecting-state-provider.component', () => {
    const actual = jest.requireActual('./selecting-state-provider.component');
    return {
        ...actual,
        useSelectingState: jest.fn(),
    };
});

jest.mock('./components/brush-tool.component', () => {
    const actual = jest.requireActual('./components/brush-tool.component');
    return {
        ...actual,
        BrushTool: () => <p>[BrushTool]</p>,
    };
});

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

const getToolSettings = jest.fn(() => ({ tool: SelectingToolType.SelectionTool }));

describe('SelectingTool', () => {
    beforeEach(() => {
        (useSelectingState as jest.Mock).mockReturnValue({
            brushSize: 20,
            activeTool: SelectingToolType.SelectionTool,
        });
    });
    const drawRect = ({
        x,
        y,
        width,
        height,
        shiftKey = false,
        releasePointer = true,
    }: {
        x: number;
        y: number;
        width: number;
        height: number;
        shiftKey?: boolean;
        releasePointer?: boolean;
    }) => {
        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: x, clientY: y });
        fireEvent.pointerDown(svg, { buttons: 1, clientX: x, clientY: y, shiftKey });

        const rect = screen.getByRole('application');
        expect(rect).toHaveAttribute('x', `${x}`);
        expect(rect).toHaveAttribute('y', `${y}`);
        expect(rect).toHaveAttribute('width', '0');
        expect(rect).toHaveAttribute('height', '0');

        fireEvent.pointerMove(svg, { clientX: x + width, clientY: y + height, shiftKey });
        expect(rect).toHaveAttribute('x', `${x}`);
        expect(rect).toHaveAttribute('y', `${y}`);
        expect(rect).toHaveAttribute('width', `${width}`);
        expect(rect).toHaveAttribute('height', `${height}`);

        releasePointer && fireEvent.pointerUp(svg);
    };

    // While we could use the spies from the annotationToolContext to check
    // that the selection tool properly updates the isSelected state of the annotations,
    // this makes it more difficult to refactor the selection tool to use different
    // methods to update the isSelected status (which is the goal of the current task)
    const renderWithScene = async (
        annotationToolContext: AnnotationToolContext,
        tasksHook: Partial<TaskContextProps> = {}
    ) => {
        const searchParams = new URLSearchParams();
        if (tasksHook.selectedTask) {
            searchParams.set('task-id', tasksHook.selectedTask.id);
        }
        jest.mocked(useSearchParams).mockImplementation(() => [searchParams, jest.fn()]);
        jest.mocked(useAnnotationToolContext).mockReturnValue(annotationToolContext);

        const App = () => {
            const scene = useAnnotationScene();
            const selectedAnnotations = scene.annotations.filter(({ isSelected }) => isSelected);

            return (
                <>
                    <SelectingTool
                        annotationToolContext={{
                            ...annotationToolContext,
                            scene,
                            // @ts-expect-error We only care about mocking selecting settings
                            getToolSettings,
                        }}
                    />
                    {/* This is used to check that we don't remove annotations in a task chain */}
                    <span>{`Selected ${selectedAnnotations.length} of ${scene.annotations.length} annotations`}</span>
                    <ul>
                        {selectedAnnotations.map((annotation) => (
                            <li key={annotation.id} aria-label={`Annotation ${annotation.id}`}>
                                {annotation.id}
                            </li>
                        ))}
                    </ul>
                </>
            );
        };

        const project = getMockedProject(tasksHook);
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => project;

        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <TaskProvider>
                    <DefaultSelectedMediaItemProvider>
                        <AnnotationSceneProvider
                            annotations={annotationToolContext.scene.annotations}
                            labels={annotationToolContext.scene.labels}
                        >
                            <TaskChainProvider
                                tasks={project.tasks}
                                selectedTask={tasksHook.selectedTask ?? null}
                                defaultLabel={null}
                            >
                                <App />
                            </TaskChainProvider>
                        </AnnotationSceneProvider>
                    </DefaultSelectedMediaItemProvider>
                </TaskProvider>
            </ProjectProvider>,
            { services: { projectService } }
        );
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    describe('clicking', () => {
        it('selects an annotation by clicking', async () => {
            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [
                    getMockedAnnotation({
                        id: '1',
                        shape: { x: 0, y: 0, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: false,
                        zIndex: 1,
                    }),
                    getMockedAnnotation({
                        id: '2',
                        shape: { x: 10, y: 10, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: false,
                        zIndex: 2,
                    }),
                ],
            });

            await renderWithScene(annotationToolContext);
            expect(screen.queryAllByLabelText(/Annotation/, { exact: false })).toHaveLength(0);

            const svg = screen.getByRole('editor');
            const pointOverFirstAnnotation = { clientX: 0, clientY: 0 };
            fireEvent.pointerDown(svg, pointOverFirstAnnotation);
            fireEvent.pointerUp(svg, pointOverFirstAnnotation);

            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(1);
            expect(screen.getByLabelText(/Annotation/, { exact: false })).toHaveTextContent('1');
        });

        it('unselects previous annotation and selects new annotation by clicking', async () => {
            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [
                    getMockedAnnotation({
                        id: '1',
                        shape: { x: 0, y: 0, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: true,
                        zIndex: 1,
                    }),
                    getMockedAnnotation({
                        id: '2',
                        shape: { x: 10, y: 10, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: false,
                        zIndex: 2,
                    }),
                ],
            });

            await renderWithScene(annotationToolContext);

            const svg = screen.getByRole('editor');

            const pointOverlapping = { clientX: 10, clientY: 10 };
            fireEvent.pointerDown(svg, pointOverlapping);
            fireEvent.pointerUp(svg, pointOverlapping);

            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(1);
            expect(screen.getByLabelText(/Annotation/, { exact: false })).toHaveTextContent('2');
        });

        it('selects additional annotations by shift clicking', async () => {
            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [
                    getMockedAnnotation({
                        id: '1',
                        shape: { x: 0, y: 0, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: true,
                        zIndex: 1,
                    }),
                    getMockedAnnotation({
                        id: '2',
                        shape: { x: 10, y: 10, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: false,
                        zIndex: 2,
                    }),
                ],
            });

            await renderWithScene(annotationToolContext);
            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(1);

            const svg = screen.getByRole('editor');

            const pointOverlapping = { clientX: 10, clientY: 10, shiftKey: true };
            fireEvent.pointerDown(svg, pointOverlapping);
            fireEvent.pointerUp(svg, pointOverlapping);

            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(2);

            // Shift clicking on a selected label deselects it
            fireEvent.pointerDown(svg, pointOverlapping);
            fireEvent.pointerUp(svg, pointOverlapping);

            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(1);
            expect(screen.getByLabelText(/Annotation/, { exact: false })).toHaveTextContent('1');
        });
    });

    describe('drawing a selection region', () => {
        it('selects annotations by drawing a selection region', async () => {
            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [
                    getMockedAnnotation({
                        id: '1',
                        shape: { x: 0, y: 0, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: false,
                        zIndex: 1,
                    }),
                    getMockedAnnotation({
                        id: '2',
                        shape: { x: 10, y: 10, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: false,
                        zIndex: 2,
                    }),
                ],
            });

            await renderWithScene(annotationToolContext);

            expect(screen.queryAllByLabelText(/Annotation/, { exact: false })).toHaveLength(0);

            drawRect({ x: 0, y: 0, width: 20, height: 20 });

            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(2);
        });

        it('adds selection by drawing a selection region while pressing shift', async () => {
            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [
                    getMockedAnnotation({
                        id: '1',
                        shape: { x: 0, y: 0, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: true,
                        zIndex: 1,
                    }),
                    getMockedAnnotation({
                        id: '2',
                        shape: { x: 10, y: 10, width: 20, height: 20, shapeType: ShapeType.Rect },
                        isSelected: false,
                        zIndex: 2,
                    }),
                ],
            });

            await renderWithScene(annotationToolContext);
            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(1);

            drawRect({ x: 22, y: 22, width: 30, height: 30, shiftKey: true });

            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(2);
        });
    });

    describe('drawing selection region without releasing pointer', () => {
        const renderAndDrawSelection = async (domain: DOMAIN) => {
            const task = getMockedTask({ id: '1', domain, labels: mockedLabels });
            const annotation = getMockedAnnotation({
                id: '1',
                shape: { x: 0, y: 0, width: 20, height: 20, shapeType: ShapeType.Rect },
                isSelected: false,
            });
            const annotationToolContext = fakeAnnotationToolContext({ annotations: [annotation] });

            await renderWithScene(annotationToolContext, { tasks: [task], selectedTask: task });

            drawRect({ x: 0, y: 0, width: 20, height: 20, releasePointer: false });
        };

        it('hides the label list for keypoint projects', async () => {
            await renderAndDrawSelection(DOMAIN.KEYPOINT_DETECTION);

            expect(screen.queryByLabelText('labels')).not.toBeInTheDocument();
        });

        it('displays the label list for non-keypoint projects', async () => {
            await renderAndDrawSelection(DOMAIN.SEGMENTATION);

            expect(screen.queryByLabelText('labels')).toBeVisible();
        });
    });

    describe('task chain aware', () => {
        const [firstLabel, ...otherLabels] = mockedLabels;
        const tasks = [
            getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: [firstLabel] }),
            getMockedTask({ id: '2', domain: DOMAIN.SEGMENTATION, labels: otherLabels }),
        ];

        // For convenience, we only consider rects for the first task and circles in the second task
        const annotations = [
            getMockedAnnotation({
                id: '1',
                shape: { x: 3, y: 3, width: 20, height: 20, shapeType: ShapeType.Rect },
                labels: [labelFromUser(firstLabel)],
                isSelected: true,
                zIndex: 1,
            }),
            getMockedAnnotation({
                id: '2',
                shape: { x: 5, y: 5, r: 5, shapeType: ShapeType.Circle },
                labels: [labelFromUser(otherLabels[0])],
                isSelected: false,
                zIndex: 2,
            }),
            getMockedAnnotation({
                id: '3',
                shape: { x: 10, y: 10, r: 5, shapeType: ShapeType.Circle },
                labels: [labelFromUser(otherLabels[0])],
                isSelected: false,
                zIndex: 3,
            }),
            // Other bounding box that's not active
            getMockedAnnotation({
                id: '4',
                shape: { x: 30, y: 30, width: 20, height: 20, shapeType: ShapeType.Rect },
                labels: [labelFromUser(firstLabel)],
                isSelected: false,
                zIndex: 1,
            }),
            getMockedAnnotation({
                id: '5',
                shape: { x: 35, y: 35, r: 5, shapeType: ShapeType.Circle },
                labels: [labelFromUser(otherLabels[0])],
                isSelected: false,
                zIndex: 2,
            }),
            getMockedAnnotation({
                id: '6',
                shape: { x: 40, y: 40, r: 5, shapeType: ShapeType.Circle },
                labels: [labelFromUser(otherLabels[0])],
                isSelected: false,
                zIndex: 3,
            }),
        ];

        // Do this to verify that we won't "delete" annotations from other tasks
        it('selects annotations from the current task', async () => {
            const annotationToolContext = fakeAnnotationToolContext({
                annotations,
            });
            await renderWithScene(annotationToolContext, { tasks, selectedTask: tasks[1] });
            const svg = screen.getByRole('editor');
            const point = { clientX: 5, clientY: 5 };
            fireEvent.pointerDown(svg, point);
            fireEvent.pointerUp(svg, point);

            // Verify that we don't remove annotations that are not selectable
            expect(screen.getByText(`Selected 2 of 6 annotations`)).toBeInTheDocument();
            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(2);

            const secondAnnotation = { clientX: 10, clientY: 10, shiftKey: true };
            fireEvent.pointerDown(svg, secondAnnotation);
            fireEvent.pointerUp(svg, secondAnnotation);

            expect(screen.getByText(`Selected 3 of 6 annotations`)).toBeInTheDocument();
            expect(screen.getAllByLabelText(/Annotation/, { exact: false })).toHaveLength(3);
        });
    });
});
