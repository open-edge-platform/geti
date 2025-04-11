// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useLocalStorage } from 'usehooks-ts';

import { useWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { LOCAL_STORAGE_KEYS } from '../../../shared/local-storage-keys';
import { getParsedLocalStorage } from '../../../shared/utils';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { ProjectExportIdentifier } from '../project.interface';

const getExportProjectKey = ({ organizationId, workspaceId }: WorkspaceIdentifier): string => {
    return `${LOCAL_STORAGE_KEYS.EXPORTING_PROJECT}-${organizationId}-${workspaceId}`;
};

const getExportingProjectLsId = (workspaceIdentifier: WorkspaceIdentifier) => {
    const exportProjectInWorkspaceContext = getParsedLocalStorage<ProjectExportIdentifier[]>(
        getExportProjectKey(workspaceIdentifier)
    );

    if (exportProjectInWorkspaceContext === null) {
        return getParsedLocalStorage<ProjectExportIdentifier[]>(LOCAL_STORAGE_KEYS.EXPORTING_PROJECT);
    }

    return exportProjectInWorkspaceContext;
};

export const useLocalStorageProject = () => {
    const workspaceIdentifier = useWorkspaceIdentifier();

    const [_lsExportProject, setLsExportProject] = useLocalStorage<ProjectExportIdentifier[] | null>(
        getExportProjectKey(workspaceIdentifier),
        () => getExportingProjectLsId(workspaceIdentifier)
    );

    const getLsExportId = (projectId: string): ProjectExportIdentifier | null => {
        const data = getExportingProjectLsId(workspaceIdentifier);

        if (data === null) {
            return null;
        }

        // Checking data that might be not be the array - backward compatibility check
        if (!Array.isArray(data)) {
            const localData = data as ProjectExportIdentifier;
            return localData.projectId === projectId ? data : null;
        }

        return data.find((item) => item.projectId === projectId) ?? null;
    };

    const setLsExportId = (data: ProjectExportIdentifier): void =>
        setLsExportProject((prevState) => [...(prevState ?? []), data]);
    const removeLsExportId = (): void => setLsExportProject(null);

    return {
        getLsExportId,
        setLsExportId,
        removeLsExportId,
    };
};
