// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useCallback, useMemo, useState } from 'react';

import { InfiniteQueryObserverResult } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { JobType } from '../../../../../core/jobs/jobs.const';
import { useProjectActions } from '../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { ProjectSortingOptions } from '../../../../../core/projects/services/project-service.interface';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE, User } from '../../../../../core/users/users.interface';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { isNonEmptyArray } from '../../../../utils';
import { JobsFilterField } from '../jobs-filter-field.component';
import { JobsTypeFilterField } from './job-types-filter-field.component';
import { FiltersType } from './jobs-dialog.interface';

interface JobsFilteringProps {
    values: FiltersType;
    onChange: (newFilters: FiltersType) => void;
}

export const JobsFiltering = ({ values, onChange }: JobsFilteringProps): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();

    const [jobFilters, setJobFilters] = useState<FiltersType>(values);
    const { projectId, userId, jobTypes } = jobFilters;

    const updateJobsFilters = (newFilters: FiltersType): void => {
        onChange(newFilters);
        setJobFilters(newFilters);
    };

    const { useGetProjects } = useProjectActions();
    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        isLoading: isLoadingProjects,
    } = useGetProjects(
        { organizationId, workspaceId },
        {
            sortBy: ProjectSortingOptions.creationDate,
            sortDir: 'dsc',
        }
    );

    const { useGetUsersQuery } = useUsers();
    const { users, isLoading: isLoadingUsers } = useGetUsersQuery(
        organizationId,
        projectId
            ? {
                  resourceId: projectId,
                  resourceType: RESOURCE_TYPE.PROJECT,
              }
            : undefined
    );

    const projects: ProjectProps[] = useMemo((): ProjectProps[] => {
        return data ? data.pages.flatMap((page) => page.projects) : [];
    }, [data]);

    const allProjectOption: { name: string; key: string } = { key: '', name: 'All projects' };
    const allUsersOption: { name: string; key: string } = { key: '', name: 'All users' };

    const projectOptions: { name: string; key: string }[] = useMemo<{ name: string; key: string }[]>(() => {
        if (!isNonEmptyArray(projects)) return [];

        return projects.map((project: ProjectProps): { name: string; key: string } => ({
            key: project.id,
            name: project.name,
        }));
    }, [projects]);

    const usersOptions: { name: string; key: string }[] = useMemo<{ name: string; key: string }[]>(() => {
        if (!isNonEmptyArray(users)) return [];

        return users.map((user: User): { name: string; key: string } => ({
            key: user.id,
            name: user.email,
        }));
    }, [users]);

    const loadMoreProjects = useCallback((): Promise<InfiniteQueryObserverResult> | undefined => {
        if (hasNextPage && !isFetchingNextPage) return fetchNextPage();
    }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

    const setSelectedProjectHandler = (key: Key | null): void => {
        const newFilterValue: undefined | string = isEmpty(key) ? undefined : (key as string);

        updateJobsFilters({ ...jobFilters, projectId: newFilterValue });
    };

    const setSelectedUserHandler = (key: Key | null): void => {
        const newFilterValue: undefined | string = isEmpty(key) ? undefined : (key as string);

        updateJobsFilters({ ...jobFilters, userId: newFilterValue });
    };

    const setSelectedJobTypesHandler = (newJobTypes: JobType[]): void => {
        updateJobsFilters({ ...jobFilters, jobTypes: newJobTypes });
    };

    return (
        <>
            <JobsFilterField
                id={'job-scheduler-filter-project'}
                ariaLabel={'Job scheduler filter project'}
                dataTestId={'job-scheduler-filter-project'}
                options={[allProjectOption, ...projectOptions]}
                value={projectId ?? allProjectOption.key}
                onSelectionChange={setSelectedProjectHandler}
                isLoading={isLoadingProjects || isFetchingNextPage}
                loadMore={loadMoreProjects}
            />
            <JobsFilterField
                id={'job-scheduler-filter-user'}
                ariaLabel={'Job scheduler filter user'}
                dataTestId={'job-scheduler-filter-user'}
                options={[allUsersOption, ...usersOptions]}
                value={userId ?? allUsersOption.key}
                onSelectionChange={setSelectedUserHandler}
                isLoading={isLoadingUsers}
            />
            <JobsTypeFilterField selectedJobTypes={jobTypes} setSelectedJobTypes={setSelectedJobTypesHandler} />
        </>
    );
};
