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

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { Annotation, AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromModel, labelFromUser } from '../../../../core/annotations/utils';
import { LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels, mockedLongLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskContextProps, useTask } from '../../providers/task-provider/task-provider.component';
import { SourceTooltip } from './label.component';
import { Labels } from './labels.component';

jest.mock('../../providers/task-chain-provider/task-chain-provider.component', () => ({
    ...jest.requireActual('../../providers/task-chain-provider/task-chain-provider.component'),
    useTaskChain: jest.fn(),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    ...jest.requireActual('./../../zoom/zoom-provider.component'),
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    ...jest.requireActual('../../providers/region-of-interest-provider/region-of-interest-provider.component'),
    useROI: jest.fn(() => ({
        roi: { x: 0, y: 0, width: 100, height: 100 },
    })),
}));

describe('Labels', (): void => {
    jest.mocked(useTaskChain).mockImplementation(() => {
        return { inputs: [], outputs: [] };
    });

    const renderApp = (
        annotation: Annotation,
        annotationToolContext: AnnotationToolContext,
        tasksHook: Partial<TaskContextProps> = {},
        showOptions = true
    ) => {
        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps(tasksHook));

        render(
            <Labels
                annotation={annotation}
                showOptions={showOptions}
                annotationToolContext={annotationToolContext}
                canEditAnnotationLabel
            />
        );
    };

    it('Allows to remove an annotation', async () => {
        const annotation: Annotation = getMockedAnnotation({
            labels: [labelFromUser(labels[0]), labelFromUser(labels[1]), labelFromUser(labels[3])],
        });
        const annotationToolContext = fakeAnnotationToolContext({ annotations: [annotation], labels });

        renderApp(annotation, annotationToolContext);

        expect(screen.getByRole('list')).toHaveAttribute('id', `${annotation.id}-labels`);

        // Should show all the user's labels
        const labelItems = screen.getAllByRole('listitem');
        expect(labelItems).toHaveLength(annotation.labels.length);
        labelItems.forEach((labelItem, idx) => {
            expect(labelItem).toHaveTextContent(annotation.labels[idx].name);
        });

        await userEvent.hover(labelItems[0]);
        fireEvent.click(screen.getByRole('button', { name: 'Remove annotation' }));

        expect(annotationToolContext.scene.removeAnnotations).toHaveBeenCalledWith([annotation]);
    });

    it('Allows to remove labels from a global annotation', async () => {
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

        const roi = { x: 0, y: 0, width: 200, height: 200 };
        const EMPTY_SHAPE = { shapeType: ShapeType.Rect as const, ...roi };

        const annotation: Annotation = getMockedAnnotation({
            labels: [labelFromUser(anomalousLabel)],
            shape: EMPTY_SHAPE,
        });
        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [annotation],
            labels,
        });

        jest.mocked(useROI).mockReturnValue({
            roi,
            image: getMockedImage(roi),
        });

        renderApp(annotation, annotationToolContext, { tasks, selectedTask: tasks[0] });

        expect(screen.getByRole('list')).toHaveAttribute('id', `${annotation.id}-labels`);

        // Should show all the user's labels
        const labelItems = screen.getAllByRole('listitem');

        await userEvent.hover(labelItems[0]);
        fireEvent.click(screen.getByRole('button', { name: 'Remove annotation' }));

        expect(annotationToolContext.scene.removeLabels).toHaveBeenCalled();
    });

    it('Allows removing a global empty label from detection task', async () => {
        const emptyLabel = getMockedLabel({
            id: 'empty-label-id',
            name: 'Empty',
            behaviour: LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL,
        });

        const tasks = [
            getMockedTask({
                id: 'detection',
                domain: DOMAIN.DETECTION,
                labels: [emptyLabel],
            }),
        ];

        const roi = { x: 0, y: 0, width: 200, height: 200 };
        const EMPTY_SHAPE = { shapeType: ShapeType.Rect as const, ...roi };

        const annotation: Annotation = getMockedAnnotation({
            labels: [labelFromUser(emptyLabel)],
            shape: EMPTY_SHAPE,
        });
        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [annotation],
            labels,
        });

        jest.mocked(useROI).mockReturnValue({
            roi,
            image: getMockedImage(roi),
        });

        renderApp(annotation, annotationToolContext, { tasks, selectedTask: tasks[0] });

        expect(screen.getByRole('list')).toHaveAttribute('id', `${annotation.id}-labels`);

        // Should show all the user's labels
        const labelItems = screen.getAllByRole('listitem');

        await userEvent.hover(labelItems[0]);
        expect(screen.getByRole('button', { name: 'Remove annotation' })).toBeInTheDocument();
    });

    it('Does not show percentage if the label is a prediction label and not user defined', () => {
        const emptyLabel = getMockedLabel({
            id: 'empty-label-id',
            name: 'Empty',
            behaviour: LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL,
        });

        const tasks = [
            getMockedTask({
                id: 'detection',
                domain: DOMAIN.DETECTION,
                labels: [emptyLabel],
            }),
        ];

        const roi = { x: 0, y: 0, width: 200, height: 200 };
        const EMPTY_SHAPE = { shapeType: ShapeType.Rect as const, ...roi };

        const annotation: Annotation = getMockedAnnotation({
            labels: [labelFromModel(emptyLabel, 100, '212', '212')],
            shape: EMPTY_SHAPE,
        });
        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [annotation],
            labels,
        });

        jest.mocked(useROI).mockReturnValue({
            roi,
            image: getMockedImage(roi),
        });

        renderApp(annotation, annotationToolContext, { tasks, selectedTask: tasks[0] });

        expect(screen.getByText('Empty')).toBeInTheDocument();
        expect(screen.queryByText('Empty (100%)')).not.toBeInTheDocument();
    });

    it("Allows to change an annotation's labels", async () => {
        const annotation: Annotation = getMockedAnnotation({
            labels: [],
        });
        const annotationToolContext = fakeAnnotationToolContext({ annotations: [annotation], labels });

        renderApp(annotation, annotationToolContext, { tasks: [getMockedTask({ labels })] });

        expect(screen.getByRole('list')).toHaveAttribute('id', `${annotation.id}-labels`);

        const selectLabel = screen.getByRole('listitem');
        expect(selectLabel).toHaveTextContent('Select label');

        await userEvent.hover(selectLabel);
        await userEvent.click(screen.getByRole('button', { name: 'Edit labels' }));
        fireEvent.focus(screen.getByLabelText('Select label'));

        expect(screen.getByLabelText('Label search results')).toBeVisible();

        const lastLabel = labels[labels.length - 1];
        await userEvent.click(screen.getByText(lastLabel.name));
        expect(annotationToolContext.scene.addLabel).toHaveBeenCalledWith(expect.objectContaining(lastLabel), [
            annotation.id,
        ]);
    });

    it('check if long label is displayed properly', () => {
        const mockedAnnotationLabels: AnnotationLabel[] = [
            {
                ...mockedLongLabels[0],
                source: {
                    userId: 'annotation-label-id-1',
                },
            },
        ];
        const mockedAnnotation = getMockedAnnotation({ labels: mockedAnnotationLabels });
        const annotationToolContext = fakeAnnotationToolContext({ annotations: [mockedAnnotation], labels });

        renderApp(mockedAnnotation, annotationToolContext, { tasks: [getMockedTask({ labels })] });

        expect(screen.getByText(mockedLongLabels[0].name)).toHaveStyle('text-overflow: ellipsis');
    });

    it('check if label is shown properly', () => {
        const mockedAnnotationLabels: AnnotationLabel[] = [
            {
                ...getMockedLabel({ name: 'princess' }),
                source: {
                    userId: 'annotation-label-id-1',
                },
            },
        ];
        const mockedAnnotation = getMockedAnnotation({ labels: mockedAnnotationLabels });
        const annotationToolContext = fakeAnnotationToolContext({ annotations: [mockedAnnotation], labels });

        renderApp(mockedAnnotation, annotationToolContext, { tasks: [getMockedTask({ labels })] });

        expect(screen.getByText('princess')).toBeInTheDocument();
    });

    it('Disable labels options', async () => {
        const annotation: Annotation = getMockedAnnotation({
            labels: [labelFromUser(labels[0]), labelFromUser(labels[1]), labelFromUser(labels[3])],
        });
        const annotationToolContext = fakeAnnotationToolContext({ annotations: [annotation], labels });

        renderApp(annotation, annotationToolContext, { tasks: [getMockedTask({ labels })] }, false);

        expect(screen.getByRole('list')).toHaveAttribute('id', `${annotation.id}-labels`);

        const labelItems = screen.getAllByRole('listitem');
        await userEvent.hover(labelItems[0]);

        expect(screen.queryByRole('button', { name: 'Edit labels' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Remove annotation' })).not.toBeInTheDocument();
    });

    describe('Anomaly', () => {
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

        it('Shows both normal and anomalous labels for global annotations', async () => {
            const annotation: Annotation = getMockedAnnotation({
                shape: EMPTY_SHAPE,
                labels: [],
            });

            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [annotation],
            });

            jest.mocked(useROI).mockReturnValue({
                roi,
                image: getMockedImage(roi),
            });

            renderApp(annotation, annotationToolContext, { tasks, selectedTask: tasks[0] });

            expect(screen.getByRole('list')).toHaveAttribute('id', `${annotation.id}-labels`);

            const selectLabel = screen.getByRole('listitem');
            expect(selectLabel).toHaveTextContent('Select label');

            await userEvent.hover(selectLabel);
            fireEvent.click(screen.getByRole('button', { name: 'Edit labels' }));
            fireEvent.focus(screen.getByLabelText('Select label'));

            await waitFor(() => {
                expect(screen.getByLabelText('Label search results')).toBeVisible();
            });

            expect(screen.getAllByRole('listitem')).toHaveLength(2);
        });

        it('Shows only anomalous label for local annotations', async () => {
            const annotation: Annotation = getMockedAnnotation({ labels: [] });

            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [annotation],
            });

            renderApp(annotation, annotationToolContext, { tasks, selectedTask: tasks[0] });

            expect(screen.getByRole('list')).toHaveAttribute('id', `${annotation.id}-labels`);

            const selectLabel = screen.getByRole('listitem');
            expect(selectLabel).toHaveTextContent('Select label');

            await userEvent.hover(selectLabel);
            fireEvent.click(screen.getByRole('button', { name: 'Edit labels' }));
            fireEvent.focus(screen.getByLabelText('Select label'));

            await waitFor(() => {
                expect(screen.getByLabelText('Label search results')).toBeVisible();
            });

            expect(screen.getAllByRole('listitem')).toHaveLength(1);
            expect(screen.getByRole('listitem')).toHaveTextContent(anomalousLabel.name);
        });
    });

    describe('SourceTooltip', () => {
        const userId = '6b3b8453-92a2-41ef-9725-63badb218504';
        const modelId = 'model-label-id-1';

        it('empty source', async () => {
            const label = {
                ...mockedLongLabels[0],
                source: {},
            };

            render(<SourceTooltip label={label} />);

            expect(screen.queryByText(`Test User`)).not.toBeInTheDocument();

            await waitFor(() => {
                expect(screen.queryByText(`Test User`)).not.toBeInTheDocument();
            });
        });

        it('userId', async () => {
            const label = {
                ...mockedLongLabels[0],
                source: {
                    userId,
                },
            };

            render(<SourceTooltip label={label} />);

            expect(await screen.findByText(`Annotated by Test User`)).toBeInTheDocument();
        });

        it('modelId', async () => {
            const label = {
                ...mockedLongLabels[0],
                score: 1,
                source: {
                    modelId,
                },
            };

            render(<SourceTooltip label={label} />);

            expect(await screen.findByText(`Annotated by model id ${modelId}`)).toBeInTheDocument();
        });

        it('accepted prediction', async () => {
            const label = {
                ...mockedLongLabels[0],
                score: 1,
                source: {
                    userId,
                    modelId,
                },
            };

            render(<SourceTooltip label={label} />);

            expect(await screen.findByText(`Annotated by Test User`)).toBeInTheDocument();
        });
    });
});
