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

import '@wessberg/pointer-events';

import { useRef } from 'react';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getImageData } from '../../../../shared/canvas-utils';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext, ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { AnnotatorContextMenuProvider } from '../../providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { TaskContextProps, TaskProvider, useTask } from '../../providers/task-provider/task-provider.component';
import { EditTool } from './edit-tool.component';

jest.mock('../../hooks/use-annotator-mode', () => ({
    useAnnotatorMode: jest.fn(() => ({ isAnnotationMode: true })),
}));

jest.mock('../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    useAnnotationScene: () => ({ hasShapePointSelected: { current: false } }),
}));

const mockROI = { x: 0, y: 0, width: 100, height: 100 };
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } }, setIsZoomDisabled: jest.fn() })),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

const renderApp = async (
    annotationToolContext: AnnotationToolContext,
    tasksHook: Partial<TaskContextProps> = {},
    isActiveLearningMode = true
) => {
    jest.mocked(useTask).mockReturnValue(mockedTaskContextProps(tasksHook));
    jest.mocked(useAnnotatorMode).mockReturnValue({
        isActiveLearningMode,
        currentMode: isActiveLearningMode ? ANNOTATOR_MODE.ACTIVE_LEARNING : ANNOTATOR_MODE.PREDICTION,
    });

    const result = render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <AnnotatorContextMenuProvider>
                    <svg>
                        <EditTool annotationToolContext={annotationToolContext} />
                    </svg>
                </AnnotatorContextMenuProvider>
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    return result;
};

describe('Edit tool', (): void => {
    const tasks = [getMockedTask({ domain: DOMAIN.SEGMENTATION })];

    it('renders empty on prediction mode', async () => {
        await renderApp(fakeAnnotationToolContext({ annotations: [] }), { tasks }, false);

        expect(screen.queryByLabelText('edit-annotations')).not.toBeInTheDocument();
    });

    it('allows editing a bounding box', async () => {
        const annotations: Annotation[] = [
            {
                id: 'rect-1',
                zIndex: 0,
                labels: [],
                shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 },
                isSelected: true,
                isHidden: false,
                isLocked: false,
            },
        ];

        const annotationToolContext = fakeAnnotationToolContext({ annotations });

        await renderApp(annotationToolContext, { tasks });

        const canvasAnnotations = screen.getByLabelText('Drag to move shape');
        expect(canvasAnnotations).toBeInTheDocument();
    });

    it('allows editing a circle', async () => {
        const annotations: Annotation[] = [
            {
                id: 'circle-1',
                zIndex: 0,
                labels: [],
                shape: { shapeType: ShapeType.Circle, x: 0, y: 0, r: 0 },
                isSelected: true,
                isHidden: false,
                isLocked: false,
            },
        ];

        const annotationToolContext = fakeAnnotationToolContext({ annotations });
        await renderApp(annotationToolContext, { tasks });

        const canvasAnnotations = screen.getByLabelText('Drag to move shape');
        expect(canvasAnnotations).toBeInTheDocument();
    });

    it('allows editing a polygon', async () => {
        const annotations: Annotation[] = [
            {
                id: 'circle-1',
                zIndex: 0,
                labels: [],
                shape: {
                    shapeType: ShapeType.Polygon,
                    points: [
                        { x: 0, y: 0 },
                        { x: 20, y: 0 },
                        { x: 20, y: 20 },
                    ],
                },
                isSelected: true,
                isHidden: false,
                isLocked: false,
            },
        ];

        const annotationToolContext = fakeAnnotationToolContext({ annotations });
        await renderApp(annotationToolContext, { tasks });

        const canvasAnnotations = screen.getByLabelText('Drag to move shape');
        expect(canvasAnnotations).toBeInTheDocument();
    });

    it('ignores annotations that are hidden', async () => {
        const annotations: Annotation[] = [
            {
                id: 'rect-1',
                zIndex: 0,
                labels: [],
                shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 },
                isSelected: true,
                isHidden: true,
                isLocked: false,
            },
        ];

        const annotationToolContext = fakeAnnotationToolContext({ annotations });
        await renderApp(annotationToolContext, { tasks });

        const canvasAnnotations = screen.queryByLabelText('Drag to move shape');
        expect(canvasAnnotations).not.toBeInTheDocument();
    });

    it('stops editing when clicking outside of the annotation', async () => {
        const annotations: Annotation[] = [getMockedAnnotation({ isSelected: true })];

        const annotationToolContext = fakeAnnotationToolContext({ annotations });

        // Render an app with an additional canvas that the user can click on so that we can
        // simulate clicking outside an annotation
        const EditToolApp = () => {
            const canvasRef = useRef<SVGSVGElement>(null);

            return (
                <div>
                    <svg ref={canvasRef} role='document'></svg>
                    <EditTool annotationToolContext={annotationToolContext} canvasRef={canvasRef} />
                </div>
            );
        };

        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks }));

        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <TaskProvider>
                    <AnnotatorContextMenuProvider>
                        <EditToolApp />
                    </AnnotatorContextMenuProvider>
                </TaskProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.getByLabelText('Drag to move shape')).toBeInTheDocument();

        const editor = screen.getByRole('document');

        // Drag with ctrl click
        fireEvent.pointerDown(editor, { ctrlKey: true });
        expect(annotationToolContext.scene.unselectAnnotation).not.toHaveBeenCalled();

        // Drag by mousewheel
        fireEvent.pointerDown(editor, { button: 1, buttons: 4 });
        expect(annotationToolContext.scene.unselectAnnotation).not.toHaveBeenCalled();

        // Click outside the annotation, thus deselecting the annotation
        fireEvent.pointerDown(editor);
        expect(annotationToolContext.scene.unselectAnnotation).toHaveBeenCalled();
    });
});

describe('editing global labels', () => {
    const image = new Image();

    image.width = 1000;
    image.height = 1000;

    const imageData = getImageData(image);

    describe('Detection -> Classification', () => {
        const tasks = [
            getMockedTask({
                id: 't-1',
                domain: DOMAIN.DETECTION,
                labels: [
                    getMockedLabel({ id: 'd-1', name: 'Object', behaviour: LABEL_BEHAVIOUR.LOCAL }),
                    getMockedLabel({
                        id: 'd-2',
                        name: 'Empty',
                        behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE,
                    }),
                ],
            }),
            getMockedTask({
                id: 't-2',
                domain: DOMAIN.CLASSIFICATION,
                labels: [
                    getMockedLabel({ id: 's-1', name: 'Deer', behaviour: LABEL_BEHAVIOUR.GLOBAL, color: 'red' }),
                    getMockedLabel({
                        id: 's-2',
                        name: 'Empty',
                        behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE,
                        color: 'green',
                    }),
                ],
            }),
        ];

        const labels = tasks.flatMap((task) => task.labels);

        it('only allows editing the label of a global annotation', async () => {
            const roi = { x: 0, y: 0, width: image.width, height: image.height };

            jest.mocked(useROI).mockReturnValueOnce({ roi, image: imageData });

            const annotations: Annotation[] = [
                getMockedAnnotation({
                    id: 'rect-1',
                    shape: { shapeType: ShapeType.Rect, ...roi },
                    labels: [labelFromUser(tasks[0].labels[1])],
                    isSelected: true,
                }),
            ];

            const annotationToolContext = fakeAnnotationToolContext({ annotations, labels });
            await renderApp(annotationToolContext, { tasks });

            const canvasAnnotations = screen.queryByLabelText('Drag to move shape');
            expect(canvasAnnotations).not.toBeInTheDocument();

            expect(screen.getByLabelText('edit-annotations')).toBeInTheDocument();
            expect(screen.getByLabelText('edit-annotations')).toHaveTextContent(annotations[0].labels[0].name);
        });

        it('does not render the shape of an empty label in task chain', async () => {
            const roi = { x: 0, y: 0, width: image.width, height: image.height };
            jest.mocked(useROI).mockReturnValueOnce({ roi, image: imageData });

            const annotations: Annotation[] = [
                getMockedAnnotation({
                    id: 'rect-1',
                    shape: { shapeType: ShapeType.Rect, ...roi },
                    labels: [labelFromUser(tasks[0].labels[0]), labelFromUser(tasks[1].labels[1])],
                    isSelected: true,
                }),
            ];

            const annotationToolContext = fakeAnnotationToolContext({
                annotations,
                labels,
            });
            await renderApp(annotationToolContext, { tasks, selectedTask: tasks[1] });

            const canvasAnnotations = screen.queryByLabelText('Drag to move shape');
            expect(canvasAnnotations).not.toBeInTheDocument();

            expect(screen.getByLabelText('edit-annotations')).toBeInTheDocument();
            expect(screen.getByLabelText('edit-annotations')).toHaveTextContent(annotations[0].labels[1].name);
        });
    });

    describe('Detection -> Segmentation', () => {
        const tasks = [
            getMockedTask({
                id: 't-1',
                domain: DOMAIN.DETECTION,
                labels: [
                    getMockedLabel({ id: 'd-1', name: 'Object', behaviour: LABEL_BEHAVIOUR.LOCAL }),
                    getMockedLabel({
                        id: 'd-2',
                        name: 'Empty',
                        behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE,
                    }),
                ],
            }),
            getMockedTask({
                id: 't-2',
                domain: DOMAIN.SEGMENTATION,
                labels: [
                    getMockedLabel({ id: 's-1', name: 'Deer', behaviour: LABEL_BEHAVIOUR.LOCAL, color: 'red' }),
                    getMockedLabel({
                        id: 's-2',
                        name: 'Empty',
                        behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE,
                        color: 'green',
                    }),
                ],
            }),
        ];

        const labels = tasks.flatMap((task) => task.labels);

        it('does render the shape of a segmentation annotation without labels', () => {
            const roi = { x: 0, y: 0, width: image.width, height: image.height };
            jest.mocked(useROI).mockReturnValueOnce({ roi, image: imageData });

            const annotations: Annotation[] = [
                getMockedAnnotation({
                    id: 'rect-1',
                    shape: { shapeType: ShapeType.Rect, ...roi },
                    labels: [labelFromUser(tasks[0].labels[0])],
                    isSelected: true,
                }),
                getMockedAnnotation({
                    id: 'rect-2',
                    shape: { shapeType: ShapeType.Rect, ...roi },
                    labels: [],
                    isSelected: true,
                }),
            ];

            const annotationToolContext = fakeAnnotationToolContext({
                annotations,
                tasks,
                labels,
                selectedTask: tasks[1],
            });
            render(
                <svg>
                    <EditTool annotationToolContext={annotationToolContext} />
                </svg>
            );

            const canvasAnnotations = screen.queryByLabelText('Drag to move shape');
            expect(canvasAnnotations).toBeInTheDocument();
        });
    });
});
