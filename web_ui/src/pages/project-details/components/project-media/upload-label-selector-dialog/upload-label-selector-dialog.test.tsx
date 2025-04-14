// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, within } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { GROUP_SEPARATOR } from '../../../../../core/labels/utils';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { Task } from '../../../../../core/projects/task.interface';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { UploadLabelSelectorDialog } from './upload-label-selector-dialog.component';

describe('UploadLabelSelectorDialog', () => {
    const classificationTask = getMockedTask({
        domain: DOMAIN.CLASSIFICATION,
        labels: [
            getMockedLabel({ id: 'Label 1', name: 'Label 1', group: 'first-group' }),
            getMockedLabel({ id: 'Label 2', name: 'Label 2', group: 'second-group' }),
        ],
    });

    const renderUploadLabelDialog = ({
        tasks,
        onCancelUpload = jest.fn(),
        onSkipAction = jest.fn(),
        onPrimaryAction = jest.fn(),
        onDismiss = jest.fn(),
    }: {
        tasks: Task[];
        onPrimaryAction?: () => void;
        onDismiss?: () => void;
        onSkipAction?: () => void;
        onCancelUpload?: () => void;
    }) => {
        return render(
            <UploadLabelSelectorDialog
                isActivated={true}
                onPrimaryAction={onPrimaryAction}
                onDismiss={onDismiss}
                onSkipAction={onSkipAction}
                tasks={tasks}
                onCancelUpload={onCancelUpload}
            />
        );
    };

    it('clicks "Skip"', async () => {
        const mockDismiss = jest.fn();
        const mockSkipAction = jest.fn();
        renderUploadLabelDialog({ tasks: [classificationTask], onDismiss: mockDismiss, onSkipAction: mockSkipAction });

        await userEvent.click(screen.getByRole('button', { name: /Skip/i }));
        expect(mockDismiss).toHaveBeenCalled();
        expect(mockSkipAction).toHaveBeenCalled();
    });

    it('should call onCancelUpload', async () => {
        const mockCancelUpload = jest.fn();

        renderUploadLabelDialog({ tasks: [classificationTask], onCancelUpload: mockCancelUpload });
        await userEvent.click(screen.getByRole('button', { name: /cancel upload/i }));
        expect(mockCancelUpload).toHaveBeenCalled();
    });

    it('should list all labels with groups', async () => {
        const tasks = [classificationTask];
        const labels = classificationTask.labels;
        renderUploadLabelDialog({ tasks });

        expect(screen.getByText('Assign a label to the uploaded images')).toBeInTheDocument();

        const numberGroups = 2;
        expect(screen.getAllByRole('listitem')).toHaveLength(labels.length + numberGroups);
        expect(screen.getByTestId('accept-button-id')).toBeDisabled();
    });

    it('should be able to assign multiple labels', async () => {
        const tasks = [classificationTask];
        const [firstLabel, secondLabel] = classificationTask.labels;
        const mockedOnPrimaryAction = jest.fn();
        const mockedOnDismiss = jest.fn();
        renderUploadLabelDialog({ tasks, onPrimaryAction: mockedOnPrimaryAction, onDismiss: mockedOnDismiss });

        // Pick the `firstLabel`
        await userEvent.click(screen.getByText(firstLabel.name));

        // Button should now be enabled
        const acceptButton = screen.getByTestId('accept-button-id');
        expect(acceptButton).toBeEnabled();
        // The container with all the selected labels should now be present
        const selectedLabelsContainer = screen.getByLabelText('label search results');

        expect(within(selectedLabelsContainer).getByText(firstLabel.name)).toBeInTheDocument();

        // Trigger LabelSearch again and pick the `secondLabel`
        await userEvent.click(screen.getByText(secondLabel.name));

        expect(screen.getByRole('checkbox', { name: firstLabel.name })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: secondLabel.name })).toBeChecked();

        expect(screen.getByText(firstLabel.name)).toBeInTheDocument();
        expect(screen.getByText(secondLabel.name)).toBeInTheDocument();

        await userEvent.click(acceptButton);
        expect(mockedOnDismiss).toHaveBeenCalled();
        expect(mockedOnPrimaryAction).toHaveBeenCalledWith([
            expect.objectContaining(firstLabel),
            expect.objectContaining(secondLabel),
        ]);
    });

    it('should be able to toggle label selection', async () => {
        const tasks = [classificationTask];
        const [firstLabel, secondLabel] = classificationTask.labels;

        renderUploadLabelDialog({ tasks });

        // Pick the `firstLabel`
        await userEvent.click(screen.getByText(firstLabel.name));

        // Button should now be enabled
        expect(screen.getByTestId('accept-button-id')).toBeEnabled();

        // The container with all the selected labels should now be present
        const selectedLabelsContainer = screen.getByLabelText('label search results');

        expect(within(selectedLabelsContainer).getByText(firstLabel.name)).toBeInTheDocument();

        // Pick the `secondLabel`
        await userEvent.click(screen.getByText(secondLabel.name));

        expect(screen.getByText(firstLabel.name)).toBeInTheDocument();
        expect(screen.getByText(secondLabel.name)).toBeInTheDocument();
        expect(screen.getByRole('checkbox', { name: firstLabel.name })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: secondLabel.name })).toBeChecked();

        await userEvent.click(screen.getByText(firstLabel.name));
        expect(screen.getByRole('checkbox', { name: firstLabel.name })).not.toBeChecked();

        await userEvent.click(screen.getByText(secondLabel.name));
        expect(screen.getByRole('checkbox', { name: secondLabel.name })).not.toBeChecked();
    });

    it('should handle adding/deleting labels with children', async () => {
        const mockVehicleLabelGroup = `vehicle-group`;
        const mockVehicleLabel = getMockedLabel({
            id: 'vehicle',
            color: '#00ff00',
            name: 'vehicle',
            group: mockVehicleLabelGroup,
            hotkey: 'ctrl+1',
        });

        const mockCarLabelGroup = `${mockVehicleLabelGroup}${GROUP_SEPARATOR}car-group`;
        const mockCarLabel = getMockedLabel({
            id: 'car',
            color: '#00ff00',
            name: 'car',
            group: mockCarLabelGroup,
            hotkey: 'ctrl+2',
            parentLabelId: 'vehicle',
        });

        const mockTeslaLabelGroup = `${mockCarLabelGroup}${GROUP_SEPARATOR}tesla-group`;
        const mockTeslaLabel = getMockedLabel({
            id: 'tesla',
            color: '#00ff00',
            name: 'tesla',
            group: mockTeslaLabelGroup,
            hotkey: 'ctrl+3',
            parentLabelId: 'car',
        });

        const mockLabelsWithChildren = [mockVehicleLabel, mockCarLabel, mockTeslaLabel];

        renderUploadLabelDialog({
            tasks: [
                getMockedTask({
                    domain: DOMAIN.CLASSIFICATION,
                    labels: mockLabelsWithChildren,
                }),
            ],
        });

        // Pick the third label
        await userEvent.click(screen.getByText(mockTeslaLabel.name));

        expect(screen.getByTestId('accept-button-id')).toBeEnabled();

        // The container with all the selected labels should now be present
        const selectedLabelsContainer = screen.getByLabelText('label search results');

        mockLabelsWithChildren.forEach((mockedLabel) => {
            expect(within(selectedLabelsContainer).queryByText(mockedLabel.name)).toBeInTheDocument();
        });

        // Delete the previously added label
        await userEvent.click(within(selectedLabelsContainer).getByText(mockVehicleLabel.name));

        // Verify that the label and its children got removed
        mockLabelsWithChildren.forEach((mockedLabel) => {
            expect(within(selectedLabelsContainer).queryByText(mockedLabel.name)).not.toBeInTheDocument();
        });
    });

    it('should handle adding labels from the same group', async () => {
        const mockTeslaLabel = getMockedLabel({
            id: 'tesla',
            color: '#00ff00',
            name: 'tesla',
            group: 'car-group',
            hotkey: 'ctrl+3',
        });

        const mockCarLabel = getMockedLabel({
            id: 'car',
            color: '#00ff00',
            name: 'car',
            group: 'car-group',
            hotkey: 'ctrl+2',
        });

        classificationTask.labels = [mockCarLabel, mockTeslaLabel];

        renderUploadLabelDialog({ tasks: [classificationTask] });

        // Pick the third label
        await userEvent.click(screen.getByText(mockTeslaLabel.name));

        expect(screen.getByTestId('accept-button-id')).toBeEnabled();

        // The container with all the selected labels should now be present
        const selectedLabelsContainer = screen.getByLabelText('label search results');

        expect(within(selectedLabelsContainer).queryByText(mockTeslaLabel.name)).toBeInTheDocument();

        // Try adding the Car label, which has the same group
        await userEvent.click(screen.getByText(mockCarLabel.name));

        // Verify that the previous label from the same group got replace
        expect(screen.getByRole('checkbox', { name: mockCarLabel.name })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: mockTeslaLabel.name })).not.toBeChecked();
    });
});
