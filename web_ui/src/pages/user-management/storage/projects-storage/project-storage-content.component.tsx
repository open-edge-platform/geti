// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
