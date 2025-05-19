// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@adobe/react-spectrum';
import { LoadingIndicator } from '@geti/ui';
import { useQueryClient } from '@tanstack/react-query';

import { useImportProjectStatusQuery } from '../../../../../core/projects/hooks/use-import-project-status.hook';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
import {
    ProjectCreatingStatus,
    ProjectImportBase,
    ProjectImportStatusValues,
} from '../../../../../providers/projects-import-provider/project-import.interface';
import { useProjectsImportProvider } from '../../../../../providers/projects-import-provider/projects-import-provider.component';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { ProjectStatusHeader } from './project-status-header.component';

import classes from './project-import.module.scss';

interface ProjectCreationStatusProps {
    importItem: ProjectCreatingStatus & ProjectImportBase;
}

export const ProjectCreationStatus = ({ importItem }: ProjectCreationStatusProps): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const queryClient = useQueryClient();

    const { fileSize, fileName, importProjectId, fileId } = importItem;

    const { patchImportProjectItem } = useProjectsImportProvider();

    useImportProjectStatusQuery({
        projectImportIdentifier: { organizationId, workspaceId, importProjectId },
        onDone: async () => {
            patchImportProjectItem(fileId, { status: ProjectImportStatusValues.CREATED });

            await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceId) });
        },
        onError: () => {
            patchImportProjectItem(fileId, { status: ProjectImportStatusValues.ERROR });
        },
    });

    return (
        <>
            <ProjectStatusHeader fileName={fileName} fileSize={fileSize} />
            <Flex gap={'size-300'} alignItems='center' UNSAFE_className={classes.importContent}>
                <LoadingIndicator size={'S'} />
                <Text>Creating...</Text>
            </Flex>
        </>
    );
};
