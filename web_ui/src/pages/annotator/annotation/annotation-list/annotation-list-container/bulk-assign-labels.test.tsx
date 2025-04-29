// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { labelFromUser } from '../../../../../core/annotations/utils';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../../test-utils/utils';
import { ProjectProvider } from '../../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { TaskContextProps, TaskProvider, useTask } from '../../../providers/task-provider/task-provider.component';
import { BulkAssignLabel } from './bulk-assign-labels.component';

jest.mock('../../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

const mockROI = getMockedROI();
const mockImage = getMockedImage(mockROI);

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

describe('BulkAssignLabel', (): void => {
    const renderApp = async (
        selectedAnnotations: readonly Annotation[],
        annotationToolContext: AnnotationToolContext,
        tasksHook: Partial<TaskContextProps> = {}
    ) => {
        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps(tasksHook));

        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
                <TaskProvider>
                    <BulkAssignLabel
                        isDisabled={false}
                        selectedAnnotations={selectedAnnotations}
                        annotationToolContext={annotationToolContext}
                    />
                </TaskProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    const labels = [
        getMockedLabel({ id: 'classification-1', name: 'label-1' }),
        getMockedLabel({ id: 'classification-2', name: 'label-2' }),
        getMockedLabel({ id: 'classification-3', name: 'label-3' }),
    ];

    it('Allows the user to add a label to selected annotations', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});

        const selectedAnnotations: ReadonlyArray<Annotation> = [getMockedAnnotation({})];

        await renderApp(selectedAnnotations, annotationToolContext, { tasks: [getMockedTask({ labels })] });

        fireEvent.click(screen.getByRole('button'));

        fireEvent.focus(screen.getByLabelText('Select label'));

        await waitFor(() => {
            expect(screen.getByLabelText('Label search results')).toBeVisible();
        });

        labels.forEach((label) => {
            expect(screen.getByRole('listitem', { name: new RegExp(label.name) })).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText(labels[0].name));

        expect(annotationToolContext.scene.addLabel).toHaveBeenCalledWith(expect.objectContaining(labels[0]), [
            selectedAnnotations[0].id,
        ]);
    });

    it('Removes the label if the selected label is assigned to each annotation', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});

        const selectedAnnotations: ReadonlyArray<Annotation> = [
            getMockedAnnotation({ labels: [labelFromUser(labels[0]), labelFromUser(labels[1])] }),
            getMockedAnnotation({ labels: [labelFromUser(labels[0]), labelFromUser(labels[1])] }),
        ];

        await renderApp(selectedAnnotations, annotationToolContext, { tasks: [getMockedTask({ labels })] });

        fireEvent.click(screen.getByRole('button'));

        fireEvent.focus(screen.getByLabelText('Select label'));

        await waitFor(() => {
            expect(screen.getByLabelText('Label search results')).toBeVisible();
        });

        fireEvent.click(screen.getByText(labels[1].name));

        expect(annotationToolContext.scene.removeLabels).toHaveBeenCalledWith(
            [expect.objectContaining(labels[1])],
            [selectedAnnotations[0].id, selectedAnnotations[1].id]
        );
    });

    it('Adds the label if the selected label is not assigned to 1 of the selected annotations', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});

        const selectedAnnotations: ReadonlyArray<Annotation> = [
            getMockedAnnotation({
                labels: [labelFromUser(labels[0]), labelFromUser(labels[1]), labelFromUser(labels[2])],
            }),
            getMockedAnnotation({ labels: [labelFromUser(labels[0]), labelFromUser(labels[1])] }),
        ];

        await renderApp(selectedAnnotations, annotationToolContext, { tasks: [getMockedTask({ labels })] });

        fireEvent.click(screen.getByRole('button'));

        fireEvent.focus(screen.getByLabelText('Select label'));

        await waitFor(() => {
            expect(screen.getByLabelText('Label search results')).toBeVisible();
        });

        fireEvent.click(screen.getByText(labels[2].name));

        expect(annotationToolContext.scene.addLabel).toHaveBeenCalledWith(expect.objectContaining(labels[2]), [
            selectedAnnotations[0].id,
            selectedAnnotations[1].id,
        ]);
    });
});
