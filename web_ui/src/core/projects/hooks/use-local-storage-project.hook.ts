// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useLocalStorage } from 'usehooks-ts';

import { WorkspaceIdentifier } from '../../../../packages/core/src/workspaces/services/workspaces.interface';
import { useWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { LOCAL_STORAGE_KEYS } from '../../../shared/local-storage-keys';
import { getParsedLocalStorage } from '../../../shared/utils';
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
