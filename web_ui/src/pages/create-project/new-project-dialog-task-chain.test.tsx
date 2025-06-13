// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OverlayTriggerState } from '@react-stately/overlays';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { LabelItemType } from '../../core/labels/label-tree-view.interface';
import { createInMemoryProjectService } from '../../core/projects/services/in-memory-project-service';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { UNIQUE_VALIDATION_MESSAGE } from './components/utils';
import { NewProjectDialogProvider } from './new-project-dialog-provider/new-project-dialog-provider.component';
import { NewProjectDialog } from './new-project-dialog.component';
import {
    clickBackButton,
    clickNextButton,
    selectAnomalyDomain,
    selectClassificationDomain,
    selectDetectionClassificationChain,
    selectDetectionSegmentationChain,
    typeIntoTextbox,
} from './test-utils';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const projectService = createInMemoryProjectService();
const createProjectMock = jest.fn();
projectService.createProject = createProjectMock;

const openImportDatasetDialog = {} as OverlayTriggerState;

const clearInput = (input: HTMLElement) => {
    fireEvent.change(input, { target: { value: '' } });
};

const renderApp = async () => {
    render(
        <NewProjectDialogProvider>
            <NewProjectDialog buttonText={'create project'} openImportDatasetDialog={openImportDatasetDialog} />
        </NewProjectDialogProvider>,
        { services: { projectService } }
    );

    const button = screen.getByText('create project');

    fireEvent.click(button);
};

describe('New project dialog - Task chain', () => {
    beforeEach(async () => {
        await renderApp();
    });

    it('should only allow creating a task-chain classification project if there are at least 2 root labels', async () => {
        await typeIntoTextbox('test project', 'Project name');
        clickNextButton();
        selectDetectionClassificationChain();
        clickNextButton();

        // Add a label for detection task
        await typeIntoTextbox('detection_label', 'Project label name input');

        // Navigate to the next task
        clickNextButton();

        const addButton = screen.getByRole('button', { name: 'Create group' });

        // Add one group and one label for classification task
        await typeIntoTextbox('labelGroup1', 'Label group name');
        fireEvent.click(addButton);

        expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();

        // Add a second label for classification task
        fireEvent.click(screen.getAllByRole('button', { name: 'add child label button' })[0]);
        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();
    });

    it('should show additional info for classification projects', async () => {
        await typeIntoTextbox('test project', 'Project name');
        clickNextButton();
        selectClassificationDomain();
        clickNextButton();

        await screen.findByLabelText('Label');

        // Should be visible on single task classification
        expect(screen.getByTestId('info-section')).toBeInTheDocument();

        // Navigate back and select anomaly task type
        clickBackButton();
        selectAnomalyDomain();

        // Should not be visible for anomaly task type
        expect(screen.queryByTestId('info-section')).not.toBeInTheDocument();

        // Select task chain type
        selectDetectionClassificationChain();
        clickNextButton();

        expect(screen.queryByTestId('info-section')).not.toBeInTheDocument();

        // Add a label for detection task and navigate to the next task (classification)
        await typeIntoTextbox('detection_label', 'Project label name input');
        clickNextButton();

        // Info section should now be visible
        expect(screen.queryByTestId('info-section')).toBeInTheDocument();
    });

    it('Check if segmentation task from task-chain has empty labels at the beginning', async () => {
        await typeIntoTextbox('test project', 'Project name');
        clickNextButton();
        selectDetectionSegmentationChain();
        clickNextButton();
        await typeIntoTextbox('cat', 'Project label name input');
        clickNextButton();

        const inputText = screen.getByRole('textbox', { name: 'Project label name input' });
        expect(inputText).toHaveValue('');
    });

    it('Create Detection > Classification project', async () => {
        await typeIntoTextbox('test', 'Project name');
        clickNextButton();
        selectDetectionClassificationChain();
        clickNextButton();
        await typeIntoTextbox('detection-label', 'Project label name input');
        clickNextButton();

        const groupTextField = screen.getByRole('textbox', { name: 'Label group name' });

        fireEvent.change(groupTextField, { target: { value: 'Root' } });

        const saveButton = screen.getByRole('button', { name: 'Create group' });
        fireEvent.click(saveButton);

        fireEvent.change(screen.getByRole('textbox', { name: 'edited name' }), { target: { value: '123' } });

        fireEvent.click(screen.getByRole('button', { name: 'add child label button' }));

        fireEvent.change(screen.getByTestId('label-tree-Label-name-input'), { target: { value: '234' } });

        const createButton = screen.getByRole('button', { name: 'Create' });
        expect(createButton).toBeEnabled();
    });

    it('Create Detection > Classification project - go back to first task and check in name, label and hotkey are properly set', async () => {
        await typeIntoTextbox('test', 'Project name');
        clickNextButton();
        selectDetectionClassificationChain();
        clickNextButton();
        await typeIntoTextbox('detection-label', 'Project label name input');

        fireEvent.click(screen.getByText('+ Add hotkey'));
        await userEvent.keyboard('{w>}r{/w}');

        clickNextButton();
        clickBackButton();

        expect(screen.getByRole('textbox', { name: 'edited hotkey' })).toBeInTheDocument();
        expect(screen.getByRole('textbox', { name: 'Project label name input' })).toHaveValue('detection-label');
    });

    it('Create Detection > Segmentation project - check if choosing same label name as in first step shows error', async () => {
        await typeIntoTextbox('test-chain', 'Project name');
        clickNextButton();
        selectDetectionSegmentationChain();
        clickNextButton();
        await typeIntoTextbox('test-label', 'Project label name input');
        clickNextButton();

        const labelTextField = screen.getByLabelText('Label');

        fireEvent.change(labelTextField, { target: { value: 'test-label' } });

        await waitFor(() =>
            expect(screen.getByText(UNIQUE_VALIDATION_MESSAGE('test-label', LabelItemType.LABEL))).toBeInTheDocument()
        );
    });

    it('Cannot add label in task chain', async () => {
        await typeIntoTextbox('test project', 'Project name');
        clickNextButton();
        selectDetectionClassificationChain();
        clickNextButton();

        await typeIntoTextbox('new label', 'Project label name input');

        expect(screen.getByRole('textbox')).toHaveValue('new label');
    });

    describe('NewProjectDialog - Check data to save', () => {
        it('Task chain - check if enter properly saves first task label', async () => {
            await typeIntoTextbox('task chain - Detection Classification', 'Project name');
            clickNextButton();
            selectDetectionClassificationChain();
            clickNextButton();

            const input = await screen.findByRole('textbox', { name: 'Project label name input' });

            fireEvent.change(input, { target: { value: 'animal' } });

            await userEvent.keyboard('{enter}');

            const groupNameInput = screen.getByRole('textbox', { name: 'Label group name' });
            fireEvent.change(groupNameInput, { target: { value: 'test' } });
            await userEvent.keyboard('{enter}');

            fireEvent.click(screen.getByRole('button', { name: 'add child label button' }));
            fireEvent.click(screen.getByRole('button', { name: 'Create' }));

            await waitFor(() => {
                expect(createProjectMock).toHaveBeenCalledWith(
                    expect.anything(),
                    'task chain - Detection Classification',
                    ['Detection', 'Classification'],
                    [
                        expect.objectContaining({
                            domain: 'Detection',
                            labels: [
                                expect.objectContaining({
                                    name: 'animal',
                                }),
                            ],
                            relation: 'Single selection',
                        }),
                        expect.objectContaining({
                            domain: 'Classification',
                            relation: 'Mixed',
                        }),
                    ],
                    true
                );
            });
        });

        it('Task chain - clearing the name disabling Next button', async () => {
            await typeIntoTextbox('task chain - Detection Classification', 'Project name');
            clickNextButton();
            selectDetectionClassificationChain();
            clickNextButton();

            const input = await screen.findByRole('textbox', { name: 'Project label name input' });

            fireEvent.input(input, { target: { value: 'animal' } });
            expect(screen.getByRole('button', { name: 'Next' })).toBeEnabled();
            clearInput(input);
            fireEvent.click(input);

            await waitFor(() => {
                expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
            });
        });

        it('Check if next function is called after clicking enter in first step of task chain', async () => {
            await typeIntoTextbox('task chain - Detection Classification', 'Project name');
            clickNextButton();
            selectDetectionClassificationChain();
            clickNextButton();

            const input = await screen.findByRole('textbox', { name: 'Project label name input' });

            fireEvent.change(input, { target: { value: 'animal' } });
            await userEvent.keyboard('{Enter}');

            expect(screen.getByRole('button', { name: 'Back' })).toBeEnabled();
            expect(screen.getByRole('button', { name: 'Create' })).toBeInTheDocument();
        });

        it('Check if next function is not called on enter when name is not valid', async () => {
            await typeIntoTextbox('task chain - Detection Classification', 'Project name');
            clickNextButton();
            selectDetectionClassificationChain();
            clickNextButton();

            const input = await screen.findByRole('textbox', { name: 'Project label name input' });

            fireEvent.change(input, { target: { value: 'animal' } });

            clearInput(input);

            await userEvent.keyboard('{Enter}');

            await waitFor(() => {
                expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
            });
            expect(screen.queryByRole('button', { name: 'Create' })).not.toBeInTheDocument();
        });
    });
});
