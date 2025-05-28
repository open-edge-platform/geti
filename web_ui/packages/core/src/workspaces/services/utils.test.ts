// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedWorkspace } from '../../../../../src/test-utils/mocked-items-factory/mocked-workspace';
import { WorkspacesResponseDTO } from '../dtos/workspace.interface';
import { getWorkspaceEntity, getWorkspaceEntityDTO, getWorkspacesEntity } from './utils';

describe('workspace service utils', () => {
    it('getWorkspaceEntity', () => {
        const mockedWorkspace = getMockedWorkspace();
        expect(getWorkspaceEntity(mockedWorkspace)).toEqual(mockedWorkspace);
    });

    it('getWorkspaceEntityDTO', () => {
        const mockedWorkspace = getMockedWorkspace();
        expect(getWorkspaceEntityDTO(mockedWorkspace)).toEqual(mockedWorkspace);
    });

    it('getWorkspacesEntity', () => {
        const workspaces = [getMockedWorkspace()];
        const data = { workspaces } as WorkspacesResponseDTO;
        expect(getWorkspacesEntity(data)).toEqual(workspaces);
    });
});
