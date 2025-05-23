// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isFunction, once } from 'lodash-es';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { JobProjectExportStatus } from '../../jobs/jobs.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { ProjectExportIdentifier } from '../project.interface';
import { JobStateToExportStatus } from '../services/api-project-service';
import { isResponseErrorQuery, isStateError } from './utils';

const isValidIdentifier = ({ projectId, workspaceId, exportProjectId }: Partial<ProjectExportIdentifier>) =>
    Boolean(workspaceId && projectId && exportProjectId);

interface useExportProjectStatusQueryProps {
    variables: Partial<ProjectExportIdentifier>;
    isExporting: boolean;
    onStart: () => void;
    onSettled?: () => void;
    onResponseError?: () => void;
}

export const useExportProjectStatusQuery = ({
    variables,
    onStart,
    onSettled,
    onResponseError,
    isExporting = false,
}: useExportProjectStatusQueryProps): UseQueryResult<JobProjectExportStatus, AxiosError> => {
    const { addNotification } = useNotification();
    const service = useApplicationServices().projectService;
    const { projectId, workspaceId, exportProjectId, organizationId } = variables;

    const callOnStartOnce = useMemo(
        () => once(onStart),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [exportProjectId]
    );

    const isQueryEnabled = isExporting && isValidIdentifier(variables);

    const exportProjectStatusQuery = useQuery<JobProjectExportStatus, AxiosError>({
        queryKey: QUERY_KEYS.PROJECT_EXPORT_STATUS_KEY(projectId as string, exportProjectId as string),
        queryFn: () => {
            if (!workspaceId || !projectId || !exportProjectId || !organizationId) {
                throw new Error("Can't fetch undefined items");
            }

            return service.exportProjectStatus({
                workspaceId,
                projectId,
                exportProjectId,
                organizationId,
            });
        },
        meta: { notifyOnError: true },
        refetchInterval: 1000,
        enabled: isQueryEnabled,
    });

    useEffect(() => {
        if (!isQueryEnabled || !exportProjectStatusQuery.isSuccess) {
            return;
        }

        const state = JobStateToExportStatus[exportProjectStatusQuery.data.state];

        callOnStartOnce();

        if (isStateError(state)) {
            addNotification({
                message: 'Project was not downloaded due to an error.',
                type: NOTIFICATION_TYPE.ERROR,
            });
        }
    }, [
        isQueryEnabled,
        exportProjectStatusQuery.isSuccess,
        exportProjectStatusQuery.data,
        addNotification,
        callOnStartOnce,
    ]);

    useEffect(() => {
        const isError = isResponseErrorQuery(exportProjectStatusQuery);

        if (isError) {
            isFunction(onResponseError) && onResponseError();
            isFunction(onSettled) && onSettled();
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [exportProjectStatusQuery?.data?.state]);

    return exportProjectStatusQuery;
};
