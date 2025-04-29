// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';
import isEmpty from 'lodash/isEmpty';

import { useProjectActions } from '../../../core/projects/hooks/use-project-actions.hook';
import { ProjectSortingOptions, ProjectsQueryOptions } from '../../../core/projects/services/project-service.interface';
import { useProjectsImportProvider } from '../../../providers/projects-import-provider/projects-import-provider.component';
import { useWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { NotFound } from '../../../shared/components/not-found/not-found.component';
import { NoProjectArea } from './components/no-projects-area/no-projects-area.component';
import { ProjectImportStatusList } from './components/project-import/project-import-status-list.component';
import { ProjectListItemSkeletonLoader } from './components/projects-list/components/project-list-item-skeleton-loader.component';
import { ProjectsList } from './components/projects-list/projects-list.component';
import { DatasetImportPanels } from './dataset-import-panels.component';
import { ProjectsActions } from './projects-actions.component';

export const LandingPageWorkspace = (): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { importItems } = useProjectsImportProvider();

    const { useGetProjects } = useProjectActions();
    const datasetImportDialogTrigger = useOverlayTriggerState({});

    const [queryOptions, setQueryOptions] = useState<ProjectsQueryOptions>({
        sortBy: ProjectSortingOptions.creationDate,
        sortDir: 'dsc',
    });

    const projectsQuery = useGetProjects({ organizationId, workspaceId }, queryOptions);

    const { data, isLoading: isLoadingProjectsQuery } = projectsQuery;

    const projects = useMemo(() => {
        return data?.pages.flatMap((page) => page.projects) ?? [];
    }, [data]);

    const hasProjects = !isEmpty(projects);
    const hasNameFilter = queryOptions.name !== undefined;
    const isLoading = isLoadingProjectsQuery;

    return (
        <Flex direction={'column'} height={'100%'}>
            <ProjectsActions
                shouldShowProjectActions={hasProjects || hasNameFilter}
                queryOptions={queryOptions}
                setQueryOptions={setQueryOptions}
                datasetImportDialogTrigger={datasetImportDialogTrigger}
            />

            <Flex
                flex={1}
                minHeight={0}
                direction={'column'}
                position={'relative'}
                UNSAFE_style={{ overflowY: 'auto' }}
                gap={'size-250'}
            >
                {!isEmpty(importItems) ? (
                    <View maxHeight={'40%'} UNSAFE_style={{ overflowY: 'auto' }}>
                        <ProjectImportStatusList />
                    </View>
                ) : null}

                <DatasetImportPanels
                    areProjectsLoading={isLoading}
                    datasetImportDialogTrigger={datasetImportDialogTrigger}
                />

                {isLoading ? (
                    <ProjectListItemSkeletonLoader itemCount={3} />
                ) : !hasProjects && hasNameFilter ? (
                    <NotFound />
                ) : hasProjects ? (
                    <View flex={1} minHeight={0}>
                        <ProjectsList projects={projects} projectsQuery={projectsQuery} />
                    </View>
                ) : (
                    <NoProjectArea openImportDatasetDialog={datasetImportDialogTrigger} />
                )}
            </Flex>
        </Flex>
    );
};
