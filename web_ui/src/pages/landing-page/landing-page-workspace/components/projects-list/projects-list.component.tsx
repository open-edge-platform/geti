// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { Loading, VirtualizedListLayout, type Selection } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { ProjectsQueryResult } from '../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { NotFound } from '../../../../../shared/components/not-found/not-found.component';
import { ProjectListItemSkeletonLoader } from './components/project-list-item-skeleton-loader.component';
import { Project } from './components/project/project.component';

interface ProjectsListProps {
    projects: ProjectProps[];
    projectsQuery: ProjectsQueryResult;
}

export const ProjectsList = ({ projects, projectsQuery }: ProjectsListProps): JSX.Element => {
    const [selected, setSelected] = useState<Selection>(new Set([]));

    useEffect(() => {
        // The user might have searched for a project (using our client side search) and
        // not found a project in the currently loaded pages.
        // In this case if there are more pages, then we want to load these before showing
        // a "Not Found" result
        if (isEmpty(projects) && projectsQuery.hasNextPage && !projectsQuery.isFetchingNextPage) {
            projectsQuery.fetchNextPage();
        }
    }, [projects, projectsQuery]);

    const handleLoadMore = () => {
        if (projectsQuery.hasNextPage && !projectsQuery.isFetchingNextPage) {
            projectsQuery.fetchNextPage();
        }
    };

    if (isEmpty(projects)) {
        if (projectsQuery.isFetchingNextPage) {
            return <Loading mode='overlay' />;
        }

        return <NotFound />;
    }

    return (
        <VirtualizedListLayout
            items={projects}
            selected={selected}
            isLoading={projectsQuery.isFetchingNextPage}
            onLoadMore={handleLoadMore}
            ariaLabel={'Projects in workspace'}
            layoutOptions={{ gap: 10 }}
            idFormatter={({ id }) => id}
            textValueFormatter={({ name }) => name}
            renderLoading={() => <ProjectListItemSkeletonLoader itemCount={1} />}
            renderItem={(item) => <Project project={item} onSelectItem={() => setSelected(new Set([item.id]))} />}
        />
    );
};
