// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { FocusScope } from 'react-aria';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { labelFromUser } from '../../../../../core/annotations/utils';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels, mockedLongLabels } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../../test-utils/utils';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { TaskContextProps, useTask } from '../../../providers/task-provider/task-provider.component';
import { AnnotationListItemContent } from './annotation-list-item-content.component';

const mockROI = getMockedROI();
const mockImage = getMockedImage(mockROI);

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    ...jest.requireActual('../../../providers/annotation-scene-provider/annotation-scene-provider.component'),
    useAnnotationScene: jest.fn(),
}));

jest.mock('../../../hooks/use-annotator-scene-interaction-state.hook', () => ({
    useIsSceneBusy: jest.fn(() => false),
}));

jest.mock('../../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        tasks: [],
        labels: [],
        selectedTask: null,
        activeDomains: [],
        isTaskChainDomainSelected: jest.fn(),
    })),
}));

jest.mock('../../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({
        project: {
            domains: [],
            tasks: [],
        },
        isSingleDomainProject: jest.fn(),
    })),
}));

const renderApp = ({
    annotation,
    context,
    tasksHook = {},
}: {
    annotation: Annotation;
    context: AnnotationToolContext;
    tasksHook?: Partial<TaskContextProps>;
}) => {
    jest.mocked(useTask).mockReturnValue(mockedTaskContextProps(tasksHook));

    return render(
        <FocusScope>
            <AnnotationListItemContent annotation={annotation} annotationToolContext={context} />
        </FocusScope>
    );
};

describe('Annotations list item content', () => {
    const mockToolContext = fakeAnnotationToolContext({ labels });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('allows the user to add a label by clicking on its content', async () => {
        const annotation = getMockedAnnotation({ labels: [] });

        await renderApp({
            annotation,
            context: mockToolContext,
            tasksHook: { tasks: [getMockedTask({ labels })] },
        });

        await waitFor(() => screen.getByText('Select label'));

        const selectLabel = screen.getByText('Select label');
        expect(selectLabel).toBeInTheDocument();

        fireEvent.click(selectLabel);

        const input = screen.getByRole('textbox', { name: 'Select label' });
        fireEvent.focus(input);

        await waitFor(() => {
            expect(screen.getByLabelText('Label search results')).toBeVisible();
        });

        fireEvent.click(screen.getByText(labels[6].name));

        expect(input).not.toBeInTheDocument();
        expect(mockToolContext.scene.addLabel).toHaveBeenCalled();
    });

    it('allows the user to add a label by double clicking on its content', async () => {
        const annotation = getMockedAnnotation({ labels: [] });

        renderApp({ annotation, context: mockToolContext, tasksHook: { tasks: [getMockedTask({ labels })] } });

        await waitFor(() => {
            screen.getByText('Select label');
        });

        const selectLabel = screen.getByText('Select label');
        expect(selectLabel).toBeInTheDocument();

        fireEvent.doubleClick(selectLabel);

        const input = screen.getByRole('textbox', { name: 'Select label' });
        fireEvent.focus(input);

        await waitFor(() => {
            expect(screen.getByLabelText('Label search results')).toBeVisible();
        });

        fireEvent.click(screen.getByText(labels[6].name));

        expect(input).not.toBeInTheDocument();
        expect(mockToolContext.scene.addLabel).toHaveBeenCalled();
    });

    it('does not allow the user to add a label by clicking on its content if it already has a label', async () => {
        const annotation = getMockedAnnotation({ labels: [labelFromUser(labels[0])] });
        renderApp({ annotation, context: mockToolContext, tasksHook: { tasks: [getMockedTask({ labels })] } });

        await waitFor(() => {
            screen.getByLabelText(`Labels of annotation with id ${annotation.id}`);
        });

        expect(screen.getByLabelText(`Labels of annotation with id ${annotation.id}`)).toHaveTextContent(
            labels[0].name
        );

        const selectLabel = screen.getByText(labels[0].name);
        expect(selectLabel).toBeInTheDocument();

        fireEvent.click(selectLabel);
        expect(screen.queryByRole('textbox', { name: 'Select label' })).not.toBeInTheDocument();
    });

    it('allows the user to add a label using the menu', async () => {
        const annotation = getMockedAnnotation({ labels: [labelFromUser(labels[0])] });

        renderApp({
            annotation,
            context: mockToolContext,
            tasksHook: { tasks: [getMockedTask({ labels })] },
        });

        await waitFor(() => {
            screen.getByText(labels[0].name);
        });

        fireEvent.mouseEnter(screen.getByLabelText('Labels of annotation with id test-rect'));

        const selectLabel = screen.getByText(labels[0].name);
        expect(selectLabel).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Show actions/ }));
        fireEvent.click(screen.getByRole('menuitem', { name: /Edit labels/ }));

        const input = screen.getByRole('textbox', { name: 'Select label' });
        fireEvent.focus(input);

        await waitFor(() => {
            expect(screen.getByLabelText('Label search results')).toBeVisible();
        });

        fireEvent.click(screen.getByText(labels[6].name));

        expect(input).not.toBeInTheDocument();
        expect(mockToolContext.scene.addLabel).toHaveBeenCalled();
    });

    it('allows the user to remove a label', async () => {
        const annotation = getMockedAnnotation({ labels: [labelFromUser(labels[0])] });
        renderApp({
            annotation,
            context: mockToolContext,
            tasksHook: { tasks: [getMockedTask({ labels })] },
        });

        await waitFor(() => {
            screen.getByText(labels[0].name);
        });

        fireEvent.mouseEnter(screen.getByLabelText('Labels of annotation with id test-rect'));

        const selectLabel = screen.getByText(labels[0].name);
        expect(selectLabel).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Show actions/ }));
        fireEvent.click(screen.getByRole('menuitem', { name: /Edit labels/ }));

        const input = screen.getByRole('textbox', { name: 'Select label' });
        fireEvent.focus(input);

        await waitFor(() => {
            expect(screen.getByLabelText('Label search results')).toBeVisible();
        });

        fireEvent.click(screen.getByText(labels[0].name));

        expect(input).not.toBeInTheDocument();
        expect(mockToolContext.scene.removeLabels).toHaveBeenCalled();
    });

    it('too long label should be truncated', async () => {
        const annotation = getMockedAnnotation({ labels: [labelFromUser(mockedLongLabels[0])] });
        renderApp({
            annotation,
            context: mockToolContext,
            tasksHook: { tasks: [getMockedTask({ labels })] },
        });

        await waitFor(() => {
            screen.getByText(mockedLongLabels[0].name);
        });

        const labelText = screen.getByText(mockedLongLabels[0].name);

        expect(labelText.parentNode).toHaveStyle('text-overflow: ellipsis');
        expect(labelText.parentNode).toHaveStyle('max-width: 200px');
    });

    it('displays a thumbnail for task chain classification tasks', async () => {
        const fakeTasks = [
            { id: 'test-task-1', title: 'test-1', labels: [], domain: DOMAIN.DETECTION },
            { id: 'test-task-2', title: 'test-2', labels: [mockedLongLabels[0]], domain: DOMAIN.CLASSIFICATION },
        ];
        const fakeSelectedTask = fakeTasks[1];

        (useProject as jest.Mock).mockImplementation(() => ({
            isTaskChainProject: true,
            project: {
                tasks: [],
            },
            isSingleDomainProject: jest.fn(),
        }));

        const annotation = getMockedAnnotation({ id: 'test-annotation', labels: [labelFromUser(mockedLongLabels[0])] });
        const context = fakeAnnotationToolContext({
            selectedTask: fakeSelectedTask,
        });

        renderApp({
            annotation,
            context,
            tasksHook: {
                selectedTask: fakeSelectedTask,
                activeDomains: [],
                isTaskChainDomainSelected: jest.fn(() => true),
                tasks: fakeTasks,
            },
        });

        expect(screen.queryByTestId(`annotation-${annotation.id}-thumbnail`)).toBeTruthy();
        expect(screen.getByLabelText('Annotated')).toBeInTheDocument();
    });

    it('does not display a thumbnail for non-classification tasks', async () => {
        const annotation = getMockedAnnotation({ id: 'test-annotation', labels: [labelFromUser(mockedLongLabels[0])] });
        const context = fakeAnnotationToolContext({});

        (useTask as jest.Mock).mockImplementation(() => ({}));

        renderApp({
            annotation,
            context,
            tasksHook: {
                selectedTask: undefined,
                activeDomains: [DOMAIN.SEGMENTATION],
                tasks: [getMockedTask({ labels })],
                isTaskChainDomainSelected: jest.fn(() => false),
            },
        });

        expect(screen.queryByTestId(`annotation-${annotation.id}-thumbnail`)).toBeFalsy();
    });

    it('displays the label names separated by inside-chevrons if labels have a parent-child relationship', async () => {
        const mockLabels = [
            labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' })),
            labelFromUser(getMockedLabel({ name: 'label-2', id: 'label-2', parentLabelId: 'label-1' })),
        ];
        const annotation = getMockedAnnotation({ id: 'test-annotation', labels: mockLabels });
        const context = fakeAnnotationToolContext({});

        renderApp({
            annotation,
            context,
            tasksHook: {
                activeDomains: [],
                tasks: [getMockedTask({ labels })],
            },
        });

        expect(screen.queryByText(`${mockLabels[0].name}`)).toBeTruthy();
        expect(screen.queryByLabelText('inside-caret')).toBeTruthy();
        expect(screen.queryByText(`${mockLabels[1].name}`)).toBeTruthy();
    });

    it('displays the label names separated by outside-chevrons if labels do not have a parent-child relationship', async () => {
        const mockLabels = [
            labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' })),
            labelFromUser(getMockedLabel({ name: 'label-2', id: 'label-2', parentLabelId: undefined })),
        ];
        const annotation = getMockedAnnotation({ id: 'test-annotation', labels: mockLabels });
        const context = fakeAnnotationToolContext({});

        renderApp({
            annotation,
            context,
            tasksHook: {
                activeDomains: [],
                tasks: [getMockedTask({ labels })],
            },
        });
        expect(screen.queryByText(`${mockLabels[0].name}`)).toBeTruthy();
        expect(screen.queryByLabelText('outside-caret')).toBeTruthy();
        expect(screen.getAllByRole('img', { hidden: true })).toHaveLength(1); // Only the SelectionIndicator is present
        expect(screen.queryByText(`${mockLabels[1].name}`)).toBeTruthy();
    });

    it('select annotation when clicking the checkbox', async () => {
        const annotation = getMockedAnnotation({
            id: 'test-annotation',
            isSelected: false,
            labels: [labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' }))],
        });
        const context = fakeAnnotationToolContext({});

        renderApp({
            annotation,
            context,
            tasksHook: {
                activeDomains: [],
                tasks: [getMockedTask({ labels })],
            },
        });

        fireEvent.click(screen.getByLabelText(`Select annotation ${annotation.id}`));
        expect(context.scene.selectAnnotation).toBeCalledWith(annotation.id);
    });

    it('unselect annotation when clicking the checkbox', async () => {
        const annotation = getMockedAnnotation({
            id: 'test-annotation',
            isSelected: true,
            labels: [labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' }))],
        });
        const context = fakeAnnotationToolContext({});

        renderApp({
            annotation,
            context,
            tasksHook: {
                activeDomains: [],
                tasks: [getMockedTask({ labels })],
            },
        });

        fireEvent.click(screen.getByLabelText(`Select annotation ${annotation.id}`));
        expect(context.scene.unselectAnnotation).toBeCalledWith(annotation.id);
    });

    it('show unlock icon and change lock', async () => {
        const annotation = getMockedAnnotation({
            id: 'test-annotation',
            isLocked: true,
            labels: [labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' }))],
        });
        const context = fakeAnnotationToolContext({});

        renderApp({
            annotation,
            context,
            tasksHook: {
                activeDomains: [],
                tasks: [getMockedTask({ labels })],
            },
        });

        fireEvent.mouseEnter(screen.getByLabelText(`Select annotation ${annotation.id}`));
        fireEvent.click(screen.getByRole('button', { name: 'unlock annotation' }));
        expect(context.scene.toggleLock).toBeCalledWith(false, annotation.id);
    });
});
