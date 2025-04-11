// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
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
