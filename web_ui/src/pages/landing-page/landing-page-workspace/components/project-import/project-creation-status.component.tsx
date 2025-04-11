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

import { Flex, Text } from '@adobe/react-spectrum';
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
import { LoadingIndicator } from '../../../../../shared/components/loading/loading-indicator.component';
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
