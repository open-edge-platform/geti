// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Suspense, useMemo, useState } from 'react';

import { Content, Divider, Flex, Grid, Heading, Loading, Text, View } from '@geti-ui/ui';
import { useProjects } from 'hooks/api/project.hook';
import { partition } from 'lodash-es';

import { version } from '../../../../package.json';
import { isNonEmptyArray, pluralize } from '../../../shared/util';
import { EmptyProjectList } from './empty-project-list/empty-project-list.component';
import { NoMatchingProjects } from './filter-projects/no-matching-projects.component';
import { ProjectFilters } from './filter-projects/project-filters.component';
import { useProjectFilters } from './filter-projects/use-project-filters.hook';
import { ImportJobsList } from './import-jobs-list/import-jobs-list.component';
import { NewProjectCard } from './new-project-card/new-project-card.component';
import { ProjectCard } from './project-card.component';
import { SORT_BY_HANDLERS, SortProjects } from './sort-projects/sort-projects.component';
import { SortBy } from './sort-projects/utils';

import backgroundStyles from '../project-background.module.scss';
import classes from './project-list.module.scss';

const MIN_NUMBER_OF_PROJECTS_TO_SHOW_FILTERS = 8;

const ProjectGrid = () => {
    const projectsQuery = useProjects();
    const projects = projectsQuery.data;
    const [sortBy, setSortBy] = useState<SortBy>('createdAt-descending');
    const hasProjects = isNonEmptyArray(projects);

    const shouldShowFilters = projects.length >= MIN_NUMBER_OF_PROJECTS_TO_SHOW_FILTERS;

    const [[activeProject], projectsWithoutActivePipeline] = partition(projects, (project) => project.active_pipeline);

    const { searchName, setSearchName, selectedTaskTypes, setSelectedTaskTypes, filteredProjects, isFiltering } =
        useProjectFilters(projectsWithoutActivePipeline);

    const sortedProjects = useMemo(() => {
        return SORT_BY_HANDLERS[sortBy](filteredProjects);
    }, [filteredProjects, sortBy]);

    const projectNames = projectsQuery.data.map((project) => project.name);

    if (!hasProjects) {
        return <EmptyProjectList />;
    }

    const matchCountLabel = `${sortedProjects.length} of ${projectsWithoutActivePipeline.length} ${pluralize(
        projectsWithoutActivePipeline.length,
        'project',
        'projects'
    )}`;

    const totalCountLabel = `${projectsWithoutActivePipeline.length} ${pluralize(
        projectsWithoutActivePipeline.length,
        'project',
        'projects'
    )}`;

    const columns = activeProject === undefined ? ['1fr'] : ['1fr', '1fr'];

    return (
        <Flex direction={'column'} gap={'size-300'} height={'100%'}>
            <Divider size={'S'} />
            <Grid columns={columns} gap={'size-300'} rows={['size-2000']}>
                <NewProjectCard />

                {activeProject !== undefined && (
                    <ProjectCard
                        item={activeProject}
                        prioritizeImage
                        projectNames={projectNames.filter((projectName) => projectName !== activeProject.name)}
                    />
                )}
            </Grid>
            {shouldShowFilters && (
                <>
                    <Divider size={'S'} />

                    <Flex width={'100%'} gap={'size-200'}>
                        <SortProjects sortBy={sortBy} onSort={setSortBy} />

                        <Divider size={'S'} orientation={'vertical'} />

                        <Flex flex={1} alignItems={'center'} gap={'size-200'}>
                            <Text UNSAFE_className={classes.projectMetadata}>
                                {isFiltering ? matchCountLabel : totalCountLabel}
                            </Text>

                            <ProjectFilters
                                searchName={searchName}
                                onSearchChange={setSearchName}
                                selectedTaskTypes={selectedTaskTypes}
                                onSelectedTaskTypesChange={setSelectedTaskTypes}
                            />
                        </Flex>
                    </Flex>
                </>
            )}
            {sortedProjects.length === 0 ? (
                <NoMatchingProjects />
            ) : (
                <Grid
                    flex={1}
                    gap={'size-300'}
                    autoRows={'size-2000'}
                    justifyContent={'center'}
                    UNSAFE_style={{ overflowY: 'auto' }}
                    columns={['1fr', '1fr']}
                >
                    {sortedProjects.map((item, index) => (
                        <ProjectCard
                            key={item.id}
                            item={item}
                            prioritizeImage={index === 0}
                            projectNames={projectNames.filter((projectName) => projectName !== item.name)}
                        />
                    ))}
                </Grid>
            )}
        </Flex>
    );
};

const AppInfo = () => {
    return <Text UNSAFE_className={classes.version}>v{version}</Text>;
};

export const ProjectList = () => {
    return (
        <View UNSAFE_className={backgroundStyles.projectBackground} height={'100%'} position={'relative'}>
            <Content height={'100%'} maxWidth={'1052px'} margin={'0 auto'} UNSAFE_className={classes.content}>
                <Flex direction={'column'} height={'100%'}>
                    <ImportJobsList />

                    <Heading
                        level={1}
                        marginBottom={'size-250'}
                        UNSAFE_style={{
                            textAlign: 'center',
                            fontSize: 'var(--spectrum-global-dimension-font-size-700)',
                        }}
                    >
                        Projects
                    </Heading>

                    <Text UNSAFE_className={classes.description}>
                        Your computer vision journey starts here.
                        <br />
                        Create projects by selecting a computer vision task, annotate your data, train models, and run
                        inference.
                    </Text>

                    <View flex={1} UNSAFE_style={{ overflow: 'auto' }}>
                        <Suspense fallback={<Loading size='M' mode='inline' />}>
                            <ProjectGrid />
                        </Suspense>
                    </View>
                </Flex>

                <View bottom={'size-150'} left={'size-150'} position={'absolute'}>
                    <AppInfo />
                </View>
            </Content>
        </View>
    );
};
