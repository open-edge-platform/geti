// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import isEmpty from 'lodash/isEmpty';

import { useProjectActions } from '../../../../core/projects/hooks/use-project-actions.hook';
import {
    ProjectSortingOptions,
    ProjectsQueryOptions,
} from '../../../../core/projects/services/project-service.interface';
import { useFirstWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { NotFound } from '../../../../shared/components/not-found/not-found.component';
import { ProjectStorageChart } from './project-storage-chart.component';
import { ProjectStorageTable } from './project-storage-table.component';

interface ProjectStorageContentProps {
    isProjectsListViewVisible: boolean;
}

export const ProjectStorageContent = ({ isProjectsListViewVisible }: ProjectStorageContentProps) => {
    const workspaceIdentifier = useFirstWorkspaceIdentifier();
    const { useGetProjects } = useProjectActions();
    const [queryOptions, setQueryOptions] = useState<ProjectsQueryOptions>({
        sortBy: ProjectSortingOptions.creationDate,
        sortDir: 'dsc',
    });
    const { isInitialLoading, data, isFetchingNextPage, fetchNextPage, hasNextPage } = useGetProjects(
        workspaceIdentifier,
        queryOptions,
        true
    );

    const projects = data?.pages?.flatMap((page) => page.projects) ?? [];

    const handleFetchNextPage = () => {
        if (hasNextPage && !isFetchingNextPage) {
            return fetchNextPage();
        }
    };

    if (isEmpty(projects) && !isInitialLoading) {
        return <NotFound heading={'You do not have any projects'} content={''} />;
    }

    return isProjectsListViewVisible ? (
        <ProjectStorageTable
            projects={projects}
            onLoadMore={handleFetchNextPage}
            isFetchingNextPage={isFetchingNextPage}
            isInitialLoading={isInitialLoading}
            onSortChange={setQueryOptions}
            queryOptions={queryOptions}
        />
    ) : (
        <ProjectStorageChart projects={projects} />
    );
};
