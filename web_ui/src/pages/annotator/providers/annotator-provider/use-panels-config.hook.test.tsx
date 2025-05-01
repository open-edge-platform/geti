// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getParsedLocalStorage } from '@shared/utils';
import { renderHook } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { AnnotatorSettingsConfig, FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { INITIAL_PROJECT_SETTINGS } from '../../../../core/user-settings/utils';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { usePanelsConfig } from './use-panels-config';

const useSettingsMock = getMockedUserProjectSettingsObject({
    saveConfig: jest.fn(),
    isSavingConfig: false,
    config: INITIAL_PROJECT_SETTINGS,
});

jest.mock('@shared/utils', () => ({
    getParsedLocalStorage: jest.fn(() => false),
}));

jest.mock('../../../../hooks/use-project-identifier/use-project-identifier', () => {
    return {
        useProjectIdentifier: jest.fn(() => {
            return {
                workspaceId: 'workspace-id',
                projectId: 'project-id',
            };
        }),
    };
});

describe('usePanelsConfig', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('counting panel is visible', async () => {
        const mockTask = getMockedTask({ id: 'task-2', domain: DOMAIN.SEGMENTATION_INSTANCE });

        renderHook(() => usePanelsConfig(mockTask, [mockTask], useSettingsMock, '1234'));

        expect(useSettingsMock.saveConfig).toHaveBeenCalledWith({
            ...useSettingsMock.config,
            [FEATURES_KEYS.COUNTING_PANEL]: {
                ...(useSettingsMock.config as AnnotatorSettingsConfig)[FEATURES_KEYS.COUNTING_PANEL],
                isEnabled: true,
            },
        });
    });

    describe('annotation panel is hidden', () => {
        it('single classification project', async () => {
            const mockTask = getMockedTask({ id: 'task-2', domain: DOMAIN.CLASSIFICATION });

            renderHook(() => usePanelsConfig(mockTask, [mockTask], useSettingsMock, '1234'));

            expect(useSettingsMock.saveConfig).toHaveBeenCalledWith({
                ...useSettingsMock.config,
                [FEATURES_KEYS.ANNOTATION_PANEL]: {
                    ...(useSettingsMock.config as AnnotatorSettingsConfig)[FEATURES_KEYS.ANNOTATION_PANEL],
                    isEnabled: false,
                },
            });
        });

        it('anomaly classification project', async () => {
            const mockTask = getMockedTask({ id: 'task-2', domain: DOMAIN.ANOMALY_CLASSIFICATION });

            renderHook(() => usePanelsConfig(mockTask, [mockTask], useSettingsMock, '1234'));

            expect(useSettingsMock.saveConfig).toHaveBeenCalledWith({
                ...useSettingsMock.config,
                [FEATURES_KEYS.ANNOTATION_PANEL]: {
                    ...(useSettingsMock.config as AnnotatorSettingsConfig)[FEATURES_KEYS.ANNOTATION_PANEL],
                    isEnabled: false,
                },
            });
        });

        it('detection-classification project', async () => {
            const mockTask = getMockedTask({ id: 'task-2', domain: DOMAIN.CLASSIFICATION });
            const detectionTaskMock = getMockedTask({ id: 'task-2', domain: DOMAIN.DETECTION });

            renderHook(() => usePanelsConfig(mockTask, [detectionTaskMock, mockTask], useSettingsMock, '1234'));

            expect(useSettingsMock.saveConfig).not.toHaveBeenCalled();
        });

        it('keep current config, user changes (localStorage)', async () => {
            jest.mocked(getParsedLocalStorage).mockReturnValueOnce(true);
            const mockTask = getMockedTask({ id: 'task-2', domain: DOMAIN.CLASSIFICATION });

            renderHook(() => usePanelsConfig(mockTask, [mockTask], useSettingsMock, '1234'));

            expect(useSettingsMock.saveConfig).not.toHaveBeenCalled();
        });
    });

    it('empty AnnotatorSettingsConfig', async () => {
        const mockTask = getMockedTask({ id: 'task-2', domain: DOMAIN.SEGMENTATION_INSTANCE });

        renderHook(() =>
            usePanelsConfig(mockTask, [mockTask], { ...useSettingsMock, config: INITIAL_PROJECT_SETTINGS }, '123')
        );

        expect(useSettingsMock.saveConfig).toHaveBeenCalled();
    });
});
