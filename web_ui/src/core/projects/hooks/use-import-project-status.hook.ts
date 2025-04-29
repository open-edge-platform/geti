// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError, isAxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { ExportStatusStateDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { ProjectImportIdentifier, ProjectImportStatus } from '../project.interface';
import { IMPORT_STATUS_ERROR } from './use-import-project.hook';
import { isStateDone, isStateError } from './utils';

interface useImportProjectStatusQueryProps {
    projectImportIdentifier: ProjectImportIdentifier;
    onDone: () => Promise<void>;
    onError: () => void;
}

const RETRY_AFTER = 1000;

export const useImportProjectStatusQuery = ({
    projectImportIdentifier,
    onDone,
    onError,
}: useImportProjectStatusQueryProps): UseQueryResult<ProjectImportStatus, AxiosError> => {
    const { addNotification } = useNotification();
    const { projectService } = useApplicationServices();

    const handleErrorRef = useRef(onError);

    const importProjectStatusQuery = useQuery<ProjectImportStatus, AxiosError, ProjectImportStatus>({
        queryKey: QUERY_KEYS.PROJECT_IMPORT_STATUS_KEY(
            projectImportIdentifier.workspaceId,
            projectImportIdentifier.importProjectId
        ),
        queryFn: async () => {
            try {
                return await projectService.getImportProjectStatus(projectImportIdentifier);
            } catch (error) {
                if (!isAxiosError(error)) {
                    throw error;
                }

                return {
                    progress: -1,
                    projectId: projectImportIdentifier.importProjectId,
                    message: getErrorMessage(error),
                    state: ExportStatusStateDTO.ERROR,
                };
            }
        },
        meta: { notifyOnError: true },
        refetchInterval: RETRY_AFTER,
    });

    useEffect(() => {
        handleErrorRef.current = onError;
    }, [onError]);

    useEffect(() => {
        if (!importProjectStatusQuery.isSuccess) {
            return;
        }

        if (isStateError(importProjectStatusQuery.data.state)) {
            handleErrorRef.current();
            addNotification({
                message: importProjectStatusQuery.data.message ?? IMPORT_STATUS_ERROR,
                type: NOTIFICATION_TYPE.ERROR,
            });
        }
    }, [importProjectStatusQuery.isSuccess, importProjectStatusQuery.data, addNotification]);

    useEffect(() => {
        if (!importProjectStatusQuery.isError) {
            return;
        }

        handleErrorRef.current();
    }, [importProjectStatusQuery.isError]);

    useEffect(() => {
        const { data } = importProjectStatusQuery;
        const isDone = data && isStateDone(data.state);

        if (isDone) {
            onDone().then();
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [importProjectStatusQuery?.data?.state]);

    return importProjectStatusQuery;
};
