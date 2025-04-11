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

import { OverlayTriggerState } from '@react-stately/overlays';
import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN } from '../../core/projects/core.interface';
import { CreateProjectProps } from '../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../core/projects/services/in-memory-project-service';
import { TaskMetadata } from '../../core/projects/task.interface';
import { WorkspaceIdentifier } from '../../core/workspaces/services/workspaces.interface';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE } from './components/utils';
import { NewProjectDialogProvider } from './new-project-dialog-provider/new-project-dialog-provider.component';
import { NewProjectDialog } from './new-project-dialog.component';
import {
    clearTextBox,
    clickBackButton,
    clickNextButton,
    selectAnomalyDomain,
    selectClassificationDomain,
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
projectService.createProject = async (
    _workspaceIdentifier: WorkspaceIdentifier,
    _name: string,
    _domains: DOMAIN[],
    _tasksLabels: TaskMetadata[]
): Promise<CreateProjectProps> => {
    return Promise.resolve({ id: 'new-project-id' } as CreateProjectProps);
};

const openImportDatasetDialog = {} as OverlayTriggerState;

const renderApp = async (
    { FEATURE_FLAG_ANOMALY_REDUCTION }: { FEATURE_FLAG_ANOMALY_REDUCTION: boolean } = {
        FEATURE_FLAG_ANOMALY_REDUCTION: false,
    }
) => {
    render(
        <NewProjectDialogProvider>
            <NewProjectDialog buttonText={'test button'} openImportDatasetDialog={openImportDatasetDialog} />
        </NewProjectDialogProvider>,
        { services: { projectService }, featureFlags: { FEATURE_FLAG_ANOMALY_REDUCTION } }
    );

    const button = screen.getByText('test button');

    expect(button).toBeInTheDocument();

    fireEvent.click(button);
};

describe('New project dialog - Single task', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('opens on button click', async () => {
        await renderApp();

        const dialog = screen.getByRole('dialog');

        expect(dialog).toBeInTheDocument();
    });

    it('consists of 3 steps, opens initially on first step', async () => {
        await renderApp();

        expect(screen.getByText('1 of 3')).toBeInTheDocument();
        expect(screen.getByText('Create project')).toBeInTheDocument();
        expect(screen.getByText('Type project name')).toBeInTheDocument();
    });

    it('Next button it enabled initially', async () => {
        await renderApp();

        expect(screen.getByRole('button', { name: 'Next' })).toBeEnabled();
    });

    it('Project name has "Project" value initially', async () => {
        await renderApp();

        expect(screen.getByRole('textbox')).toHaveValue('Project');
    });

    it("Next button is enabled when project's name is not empty", async () => {
        await renderApp();

        await clearTextBox('Project name');

        expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();

        await typeIntoTextbox('test', 'Project name');

        expect(screen.getByRole('button', { name: 'Next' })).toBeEnabled();
    });

    it("When there are some labels 'create' button is enabled", async () => {
        await renderApp();
        clickNextButton();
        clickNextButton();

        const input = await screen.findByLabelText('Label');

        await userEvent.type(input, 'test_label');

        const addButton = screen.getByRole('button', { name: 'Create label' });
        fireEvent.click(addButton);
        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();
    });

    it("When there are no labels 'create' button is disabled", async () => {
        await renderApp();

        clickNextButton();
        clickNextButton();

        await screen.findByLabelText('Label');

        expect(screen.getByRole('button', { name: 'Create' })).not.toBeEnabled();
    });

    it('Should not allow adding labels to anomaly projects [FEATURE_FLAG_ANOMALY_REDUCTION: true]', async () => {
        await renderApp({ FEATURE_FLAG_ANOMALY_REDUCTION: true });

        clickNextButton();
        selectAnomalyDomain();

        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();
    });

    it('Should not allow adding labels to anomaly projects [FEATURE_FLAG_ANOMALY_REDUCTION: false]', async () => {
        await renderApp();

        clickNextButton();
        selectAnomalyDomain();

        // Anomaly classification selected by default
        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();

        // Select Anomaly Detection
        fireEvent.click(screen.getByTestId('anomaly-detection-card-id'));
        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();

        // Select Anomaly Segmentation
        fireEvent.click(screen.getByTestId('anomaly-segmentation-card-id'));
        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();
    });

    it('should allow creating a single-task classification project if there are at least 2 labels', async () => {
        await renderApp();

        clickNextButton();
        selectClassificationDomain();
        clickNextButton();

        await screen.findByLabelText('Label');

        expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();

        // Add one label
        await typeIntoTextbox('test_label', 'Project label name input');

        const addButton = screen.getByRole('button', { name: 'Create label' });

        fireEvent.click(addButton);

        expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();

        // Add another label
        await typeIntoTextbox('test_label_2', 'Project label name input');
        fireEvent.click(addButton);

        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();
    });

    it('Select Chained tasks shows 4 steps', async () => {
        await renderApp();

        clickNextButton();
        const tab = screen.getByRole('tab', { name: 'Chained tasks' });
        fireEvent.click(tab);

        expect(screen.getByText('2 of 4')).toBeVisible();

        const detectionClassificationChain = screen.getByTestId('Detection-Classification');
        expect(detectionClassificationChain).toBeInTheDocument();

        const detectionSegmentationChain = screen.getByTestId('Detection-Segmentation');
        expect(detectionSegmentationChain).toBeInTheDocument();
    });

    it('Click previous step when defining labels - next button should be visible and enabled. User should be back to selecting template step', async () => {
        await renderApp();

        clickNextButton();
        clickNextButton();

        await screen.findByLabelText('Label');

        clickBackButton();

        expect(screen.getByRole('button', { name: 'Next' })).toBeEnabled();
        expect(screen.getByText('2 of 3')).toBeInTheDocument();
        expect(screen.getByText('Select task type')).toBeInTheDocument();
    });

    it("Type names contains only spaces - error should be displayed and 'next' button should be disabled", async () => {
        await renderApp();

        await clearTextBox('Project name');

        await typeIntoTextbox('   ', 'Project name');
        expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
        expect(screen.getByText(REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE)).toBeInTheDocument();
    });
});
