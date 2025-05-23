// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { paths } from '@geti/core';
import { useDeploymentConfigQuery } from '@geti/core/src/services/use-deployment-config-query.hook';
import { invoke } from 'lodash-es';
import { Navigate } from 'react-router-dom';
import { useLocalStorage } from 'usehooks-ts';

import { Task } from '../core/projects/task.interface';
import { useWorkspacesApi } from '../core/workspaces/hooks/use-workspaces.hook';
import { useModelIdentifier } from '../hooks/use-model-identifier/use-model-identifier.hook';
import { useOrganizationIdentifier } from '../hooks/use-organization-identifier/use-organization-identifier.hook';
import { useDatasetIdentifier } from '../pages/annotator/hooks/use-dataset-identifier.hook';
import { ErrorLayout } from '../pages/errors/error-layout/error-layout.component';
import { ResourceNotFound } from '../pages/errors/resource-not-found/resource-not-found.component';
import { useProject } from '../pages/project-details/providers/project-provider/project-provider.component';
import { useWorkspaceIdentifier } from '../providers/workspaces-provider/use-workspace-identifier.hook';
import { LOCAL_STORAGE_KEYS } from '../shared/local-storage-keys';

export const RedirectToOptimizedModel = () => {
    const modelIdentifier = useModelIdentifier();

    return <Navigate to={paths.project.models.model.modelVariants.index(modelIdentifier)} replace />;
};

export const RedirectToOpenVino = () => {
    const modelIdentifier = useModelIdentifier();

    return <Navigate to={paths.project.models.model.modelVariants.openVino(modelIdentifier)} replace />;
};

export const RedirectToWorkspace = () => {
    const { organizationId } = useOrganizationIdentifier();

    // Redirect to the first available workspace
    const { useWorkspacesQuery } = useWorkspacesApi(organizationId);
    const { data: workspaces } = useWorkspacesQuery();
    const workspaceId = workspaces.at(0)?.id;

    // Show an error if we are unable to load workspaces
    if (workspaceId === undefined) {
        return (
            <ErrorLayout>
                <ResourceNotFound />
            </ErrorLayout>
        );
    }

    return <Navigate to={paths.workspace({ organizationId, workspaceId })} replace />;
};

export const RedirectToDatasetMedia = () => {
    const datasetIdentifier = useDatasetIdentifier();

    return <Navigate to={paths.project.dataset.media(datasetIdentifier)} replace />;
};

export const RedirectToUsersProfile = () => {
    const { organizationId } = useOrganizationIdentifier();
    return <Navigate to={paths.account.profile({ organizationId })} replace />;
};

export const CallbackRedirect = () => {
    const [redirectLocation] = useLocalStorage(LOCAL_STORAGE_KEYS.INTENDED_PATH_BEFORE_AUTHENTICATION, paths.root({}));

    // We don't want the user to remain on the /callback route as this does not render anything
    if (redirectLocation === paths.authProviderCallback({})) {
        return <Navigate to={paths.root({})} />;
    }

    return <Navigate to={redirectLocation ?? paths.root({})} />;
};

export const RedirectIfSaaS = ({ children }: { children: ReactNode }) => {
    const config = useDeploymentConfigQuery();

    if (config.data?.auth.type !== 'dex') {
        return <Navigate to={paths.root({})} replace />;
    }

    return <>{children}</>;
};

export const RedirectIfTaskIs = ({
    to,
    children,
    predicate,
}: {
    to: keyof typeof paths.project;
    children: ReactNode;
    predicate: (task: Task) => boolean;
}) => {
    const { project } = useProject();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();

    if (project.tasks.some(predicate)) {
        return (
            <Navigate to={invoke(paths.project, to, { organizationId, workspaceId, projectId: project.id })} replace />
        );
    }

    return <>{children}</>;
};
