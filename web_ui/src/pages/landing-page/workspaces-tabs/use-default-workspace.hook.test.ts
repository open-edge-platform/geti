// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';

import { WORKSPACES_SETTINGS_KEYS, WorkspacesConfig } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { useDefaultWorkspace } from './use-default-workspace.hook';

jest.mock('../../../core/user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../../core/user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(),
}));

const renderUseDefaultWorkspaceHook = (workspaces: WorkspaceEntity[]) => {
    return renderHookWithProviders(() => useDefaultWorkspace(workspaces));
};

const mockedWorkspaces = [
    getMockedWorkspace({ id: '1', name: 'Workspace 1' }),
    getMockedWorkspace({ id: '2', name: 'Workspace 2' }),
    getMockedWorkspace({ id: '3', name: 'Workspace 3' }),
    getMockedWorkspace({ id: '4', name: 'Workspace 4' }),
];

describe('useDefaultWorkspace', () => {
    it('check defaultWorkspaceId and reorderedWorkspaceList', async () => {
        jest.mocked(useUserGlobalSettings).mockReturnValue({
            saveConfig: jest.fn(),
            isSavingConfig: false,
            config: { [WORKSPACES_SETTINGS_KEYS.DEFAULT_WORKSPACE]: { id: '2' } },
        });

        const { result } = renderUseDefaultWorkspaceHook(mockedWorkspaces);

        expect(result).toStrictEqual({
            current: {
                defaultWorkspaceId: '2',
                reorderedWorkspaces: [
                    mockedWorkspaces[1],
                    mockedWorkspaces[0],
                    mockedWorkspaces[2],
                    mockedWorkspaces[3],
                ],
            },
        });
    });

    it('checkValues when there is no default workspace', async () => {
        jest.mocked(useUserGlobalSettings).mockReturnValue({
            saveConfig: jest.fn(),
            isSavingConfig: false,
            config: {} as WorkspacesConfig,
        });

        const { result } = renderUseDefaultWorkspaceHook(mockedWorkspaces);

        expect(result).toStrictEqual({
            current: {
                defaultWorkspaceId: undefined,
                reorderedWorkspaces: mockedWorkspaces,
            },
        });
    });
});
