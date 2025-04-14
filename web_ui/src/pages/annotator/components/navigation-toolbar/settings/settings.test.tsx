// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { FEATURES_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../../core/user-settings/services/user-settings.interface';
import { initialAnnotatorConfig } from '../../../../../core/user-settings/utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { getMockedUserProjectSettingsObject } from '../../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask, mockedTaskContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { Settings } from './settings.component';

jest.mock('../../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({})),
}));

describe('Settings', () => {
    const saveConfigMock = jest.fn();
    const mockSettings = getMockedUserProjectSettingsObject({
        saveConfig: saveConfigMock,
    });

    const renderSettingsDialog = async (
        settings: UseSettings<UserProjectSettings>,
        domain: DOMAIN = DOMAIN.DETECTION
    ) => {
        const tasks = [getMockedTask({ domain })];
        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask: tasks[0] }));
        await render(<Settings settings={settings} />);

        fireEvent.click(screen.getByTestId('settings-icon'));
    };

    it('should render a dialog with the correct settings', async () => {
        await renderSettingsDialog(mockSettings);

        const annotationSwitch = screen.queryByTestId(
            `${idMatchingFormat(initialAnnotatorConfig.annotation.title)}-panel-switch-id`
        );
        const countingSwitch = screen.queryByTestId(
            `${idMatchingFormat(initialAnnotatorConfig.counting.title)}-panel-switch-id`
        );
        const datasetSwitch = screen.queryByTestId(
            `${idMatchingFormat(initialAnnotatorConfig.dataset.title)}-panel-switch-id`
        );

        expect(annotationSwitch).toHaveProperty('checked', true);
        expect(countingSwitch).toHaveProperty('checked', false);
        expect(datasetSwitch).toHaveProperty('checked', true);
    });

    it('should disable "save" button by default', async () => {
        await renderSettingsDialog(mockSettings);

        const saveButton = screen.getByTestId('save-settings-dialog-id');

        expect(saveButton).toBeDisabled();
    });

    it('should enable "save" button if the user makes changes to the original config', async () => {
        await renderSettingsDialog(mockSettings);

        const annotationSwitch = screen.getByTestId(
            `${idMatchingFormat(initialAnnotatorConfig.annotation.title)}-panel-switch-id`
        );

        const saveButton = screen.getByTestId('save-settings-dialog-id');
        expect(saveButton).toBeDisabled();

        fireEvent.click(annotationSwitch);

        expect(saveButton).toBeEnabled();
    });

    it('should show the save button with a loading state if it is saving the new config', async () => {
        const mockSettingsLoading = getMockedUserProjectSettingsObject({
            isSavingConfig: true,
        });

        await renderSettingsDialog(mockSettingsLoading);

        const progressbar = await screen.findByRole('progressbar', { name: /Save settings pending/, hidden: true });

        expect(progressbar).toBeVisible();
    });

    it('should not show the counting panel in the classification', async () => {
        const mockSettingsLoading = getMockedUserProjectSettingsObject({
            isSavingConfig: true,
        });

        await renderSettingsDialog(mockSettingsLoading, DOMAIN.CLASSIFICATION);
        const countingSwitch = screen.queryByTestId(
            `${idMatchingFormat(initialAnnotatorConfig.counting.title)}-panel-switch-id`
        );

        expect(countingSwitch).not.toBeInTheDocument();
    });

    it('should execute saveConfig callback properly', async () => {
        const mockSettingsCallback = getMockedUserProjectSettingsObject({
            isSavingConfig: false,
        });

        await renderSettingsDialog(mockSettingsCallback);

        const saveButton = screen.getByTestId('save-settings-dialog-id');

        expect(saveButton).toBeDisabled();

        const countingSwitch = screen.getByTestId(
            `${idMatchingFormat(initialAnnotatorConfig.counting.title)}-panel-switch-id`
        );

        fireEvent.click(countingSwitch);

        expect(saveButton).not.toBeDisabled();
        fireEvent.click(saveButton);

        expect(mockSettingsCallback.saveConfig).toHaveBeenCalledWith({
            ...mockSettingsCallback.config,
            [FEATURES_KEYS.COUNTING_PANEL]: { ...initialAnnotatorConfig.counting, isEnabled: true },
        });
    });
});
