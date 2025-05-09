// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useCallback, useEffect, useMemo, useState } from 'react';

import { InfiniteQueryObserverResult } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { JobType } from '../../../../../core/jobs/jobs.const';
import { useProjectActions } from '../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { ProjectSortingOptions } from '../../../../../core/projects/services/project-service.interface';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE, User } from '../../../../../core/users/users.interface';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { hasEqualId, isNonEmptyArray } from '../../../../utils';
import { JobsFilterField } from '../jobs-filter-field.component';
import { JobsTypeFilterField } from './job-types-filter-field.component';

interface JobsFilteringDefaultValuesProps {
    projectIdFilter: string | undefined;
    userIdFilter: string | undefined;
    jobTypeFilter: JobType[];
}

interface JobsFilteringProps {
    defaultValues: JobsFilteringDefaultValuesProps;
    onChange: (projectId: string | undefined, userId: string | undefined, type: JobType[]) => void;
}

export const JobsFiltering = ({ defaultValues, onChange }: JobsFilteringProps): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();

    const { projectIdFilter, userIdFilter, jobTypeFilter } = defaultValues;

    const [selectedProject, setSelectedProject] = useState<string | undefined>(projectIdFilter);
    const [selectedUser, setSelectedUser] = useState<string | undefined>(userIdFilter);
    const [selectedJobTypes, setSelectedJobTypes] = useState<JobType[]>(jobTypeFilter);

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
        selectedProject
            ? {
                  resourceId: selectedProject,
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

        setSelectedProject(newFilterValue);
    };

    const setSelectedUserHandler = (key: Key | null): void => {
        const newFilterValue: undefined | string = isEmpty(key) ? undefined : (key as string);

        setSelectedUser(newFilterValue);
    };

    useEffect(() => {
        if (isLoadingUsers) return;

        const isSelectedUserInProject: boolean | undefined = users?.some(hasEqualId(selectedUser));

        if (!!isSelectedUserInProject) return;

        setSelectedUser(undefined);
        onChange(selectedProject, undefined, selectedJobTypes);
    }, [isLoadingUsers, onChange, selectedJobTypes, selectedProject, selectedUser, users]);

    useEffect(() => {
        onChange(selectedProject, selectedUser, selectedJobTypes);
    }, [selectedProject, selectedUser, selectedJobTypes, onChange]);

    return (
        <>
            <JobsFilterField
                id={'job-scheduler-filter-project'}
                ariaLabel={'Job scheduler filter project'}
                dataTestId={'job-scheduler-filter-project'}
                options={[allProjectOption, ...projectOptions]}
                value={selectedProject ?? allProjectOption.key}
                onSelectionChange={setSelectedProjectHandler}
                isLoading={isLoadingProjects || isFetchingNextPage}
                loadMore={loadMoreProjects}
            />
            <JobsFilterField
                id={'job-scheduler-filter-user'}
                ariaLabel={'Job scheduler filter user'}
                dataTestId={'job-scheduler-filter-user'}
                options={[allUsersOption, ...usersOptions]}
                value={selectedUser ?? allUsersOption.key}
                onSelectionChange={setSelectedUserHandler}
                isLoading={isLoadingUsers}
            />
            <JobsTypeFilterField selectedJobTypes={selectedJobTypes} setSelectedJobTypes={setSelectedJobTypes} />
        </>
    );
};
