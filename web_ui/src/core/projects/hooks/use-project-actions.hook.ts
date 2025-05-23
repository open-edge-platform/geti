// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import {
    InfiniteData,
    QueryKey,
    queryOptions,
    useInfiniteQuery,
    UseInfiniteQueryResult,
    useMutation,
    UseMutationResult,
    useQuery,
    useQueryClient,
    UseQueryResult,
    useSuspenseQuery,
    UseSuspenseQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isEmpty, omit } from 'lodash-es';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { useFeatureFlags } from '../../feature-flags/hooks/use-feature-flags.hook';
import QUERY_KEYS from '../../requests/query-keys';
import { getErrorMessage } from '../../services/utils';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { DOMAIN, ProjectIdentifier } from '../core.interface';
import { DatasetIdentifier } from '../dataset.interface';
import { CreateProjectProps, EditProjectProps, ProjectName, ProjectProps } from '../project.interface';
import { ProjectService, ProjectsQueryOptions } from '../services/project-service.interface';
import { TaskMetadata } from '../task.interface';
import { getEditTasksEntity } from './utils';

interface UseCreateProjectMutation {
    workspaceIdentifier: WorkspaceIdentifier;
    name: string;
    domains: DOMAIN[];
    projectTypeMetadata: TaskMetadata[];
}

interface UseEditLabelParams {
    tasksMetadata: TaskMetadata[];
    project: EditProjectProps;
    datasetIdentifier: DatasetIdentifier;
    shouldRevisit: boolean;
}

interface UseEditProjectParams {
    projectIdentifier: ProjectIdentifier;
    project: ProjectProps;
}

interface UseEditProjectParamsContext {
    previousProjects: (InfiniteData<ProjectQueryPageData> | undefined[]) | undefined;
    previousProject: ProjectProps | undefined;
}

type ProjectQueryPageData = {
    projects: ProjectProps[];
    nextPage: string | null | undefined;
};

export type ProjectsQueryResult = UseInfiniteQueryResult<InfiniteData<ProjectQueryPageData>, AxiosError>;

interface UseProjectActions {
    createProjectMutation: UseMutationResult<CreateProjectProps, AxiosError, UseCreateProjectMutation>;
    deleteProjectMutation: UseMutationResult<string, AxiosError, ProjectIdentifier>;
    editProjectLabelsMutation: UseMutationResult<ProjectProps, AxiosError, UseEditLabelParams>;
    useGetProject: (projectIdentifier: ProjectIdentifier) => UseQueryResult<ProjectProps, AxiosError>;
    useSuspenseGetProject: (projectIdentifier: ProjectIdentifier) => UseSuspenseQueryResult<ProjectProps, AxiosError>;
    useGetProjects: (
        workspaceIdentifier: WorkspaceIdentifier,
        queryOptions: ProjectsQueryOptions,
        withSize?: boolean
    ) => ProjectsQueryResult;
    useGetProjectNames: (
        workspaceIdentifier: WorkspaceIdentifier
    ) => UseQueryResult<{ projects: ProjectName[] }, AxiosError>;
    editProjectMutation: UseMutationResult<
        ProjectProps | undefined,
        AxiosError,
        UseEditProjectParams,
        UseEditProjectParamsContext
    >;
}

const projectsUpdater =
    (formatter: (projects: ProjectProps[]) => ProjectProps[]) =>
    (oldData: InfiniteData<ProjectQueryPageData> | undefined) => {
        if (oldData === undefined) {
            return oldData;
        }

        const pages = oldData.pages.map((page) => ({
            ...page,
            projects: formatter(page.projects),
        }));

        return { ...oldData, pages };
    };

const ERROR_MESSAGE = 'Failed to load project page - something went wrong. Please, try again later.';
const PROJECTS_ERROR_MESSAGE = 'Failed to load the projects - something went wrong. Please, try again later.';

const projectQueryOptions = (projectIdentifier: ProjectIdentifier, projectService: ProjectService) => {
    return queryOptions<ProjectProps, AxiosError>({
        queryKey: QUERY_KEYS.PROJECT_KEY(projectIdentifier),
        queryFn: () => projectService.getProject(projectIdentifier),
        meta: { notifyOnError: true, errorMessage: ERROR_MESSAGE },
    });
};

export const useProjectActions = (): UseProjectActions => {
    const client = useQueryClient();
    const { addNotification } = useNotification();
    const { projectService } = useApplicationServices();
    const { FEATURE_FLAG_ANOMALY_REDUCTION } = useFeatureFlags();

    const onError = (error: AxiosError) => {
        addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
    };

    const useGetProject = (projectIdentifier: ProjectIdentifier) => {
        return useQuery<ProjectProps, AxiosError>(projectQueryOptions(projectIdentifier, projectService));
    };

    const useSuspenseGetProject = (projectIdentifier: ProjectIdentifier) => {
        return useSuspenseQuery(projectQueryOptions(projectIdentifier, projectService));
    };

    const useGetProjects = (
        workspaceIdentifier: WorkspaceIdentifier,
        projectsQueryOptions: ProjectsQueryOptions,
        withSize = false
    ) => {
        return useInfiniteQuery<
            ProjectQueryPageData,
            AxiosError,
            InfiniteData<ProjectQueryPageData>,
            QueryKey,
            NextPageURL
        >({
            queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceIdentifier.workspaceId, projectsQueryOptions, withSize),
            queryFn: ({ pageParam: nextPage = null }) =>
                projectService.getProjects(workspaceIdentifier, projectsQueryOptions, nextPage, withSize),
            getPreviousPageParam: () => undefined,
            getNextPageParam: ({ nextPage }) => (nextPage === '' ? undefined : nextPage),
            meta: { notifyOnError: true, errorMessage: PROJECTS_ERROR_MESSAGE },
            initialPageParam: null,
        });
    };

    const useGetProjectNames = (workspaceIdentifier: WorkspaceIdentifier) => {
        return useQuery<{ projects: ProjectName[] }, AxiosError>({
            queryKey: QUERY_KEYS.PROJECT_NAMES(workspaceIdentifier),
            queryFn: () => projectService.getProjectNames(workspaceIdentifier),
        });
    };

    const createProjectMutation = useMutation({
        mutationFn: ({ workspaceIdentifier, name, domains, projectTypeMetadata }: UseCreateProjectMutation) =>
            projectService.createProject(
                workspaceIdentifier,
                name,
                domains,
                projectTypeMetadata,
                FEATURE_FLAG_ANOMALY_REDUCTION
            ),

        onError,
        onSettled: (_, __, { workspaceIdentifier }) => {
            client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceIdentifier.workspaceId) });
        },
    });

    const editProjectMutation = useMutation<
        ProjectProps | undefined,
        AxiosError,
        UseEditProjectParams,
        UseEditProjectParamsContext
    >({
        mutationFn: ({ projectIdentifier, project }) => {
            return projectService.editProject(projectIdentifier, project, FEATURE_FLAG_ANOMALY_REDUCTION);
        },
        onMutate: ({ projectIdentifier, project }) => {
            const queryKey = QUERY_KEYS.PROJECTS_KEY(projectIdentifier.workspaceId);
            const previousProjects = client.getQueryData<InfiniteData<ProjectQueryPageData> | undefined[]>(queryKey);

            const previousProject = client.getQueryData<ProjectProps>(QUERY_KEYS.PROJECT_KEY(projectIdentifier));

            client.setQueriesData<InfiniteData<ProjectQueryPageData> | undefined>(
                { queryKey },
                projectsUpdater((projects) =>
                    projects.map((prevProject) =>
                        prevProject.id === projectIdentifier.projectId ? project : prevProject
                    )
                )
            );

            client.setQueryData<ProjectProps>(QUERY_KEYS.PROJECT_KEY(projectIdentifier), (oldData) => {
                if (oldData === undefined) {
                    return oldData;
                }

                if (isEmpty(project.datasets) && !isEmpty(oldData.datasets)) {
                    return {
                        ...oldData,
                        ...omit(project, 'datasets'),
                    };
                }

                return {
                    ...oldData,
                    ...project,
                };
            });

            return {
                previousProjects,
                previousProject,
            };
        },
        onError: (error, { projectIdentifier }, context) => {
            client.setQueryData(QUERY_KEYS.PROJECTS_KEY(projectIdentifier.workspaceId), context?.previousProjects);
            client.setQueryData(QUERY_KEYS.PROJECT_KEY(projectIdentifier), context?.previousProject);
            onError(error);
        },
        onSettled: async (_, __, { projectIdentifier }) => {
            await Promise.all([
                client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(projectIdentifier.workspaceId) }),
                client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_KEY(projectIdentifier) }),
            ]);
        },
    });

    const deleteProjectMutation = useMutation<string, AxiosError, ProjectIdentifier>({
        mutationFn: projectService.deleteProject,
        onSuccess: (_, variables: ProjectIdentifier) => {
            const { workspaceId } = variables;

            return client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceId) });
        },
        onError,
    });

    const editProjectLabelsMutation = useMutation({
        mutationFn: ({ datasetIdentifier, tasksMetadata, project, shouldRevisit }: UseEditLabelParams) => {
            const { organizationId, workspaceId, projectId } = datasetIdentifier;

            const tasks = getEditTasksEntity(project.tasks, tasksMetadata, shouldRevisit);

            return projectService.editProject(
                { organizationId, workspaceId, projectId },
                { ...project, tasks },
                FEATURE_FLAG_ANOMALY_REDUCTION
            );
        },

        onError: (error: AxiosError) => {
            const message = getErrorMessage(error) || 'Labels were not updated due to an error';
            addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    return {
        useGetProject,
        useSuspenseGetProject,
        useGetProjects,
        useGetProjectNames,
        editProjectMutation,
        createProjectMutation,
        deleteProjectMutation,
        editProjectLabelsMutation,
    };
};
