// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentType, forwardRef, LegacyRef, useEffect } from 'react';

import { View } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { Components, Virtuoso } from 'react-virtuoso';

import { ProjectsQueryResult } from '../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { NotFound } from '../../../../../shared/components/not-found/not-found.component';
import { UnwrapProps } from '../../../../../types-utils/types';
import { LoadingOverlay } from '../../../../project-details/components/project-media/loading-overlay.component';
import { ProjectListItemSkeletonLoader } from './components/project-list-item-skeleton-loader.component';
import { Project } from './components/project/project.component';

import classes from './projects-list.module.scss';

interface ProjectsListProps {
    projects: ProjectProps[];
    projectsQuery: ProjectsQueryResult;
}

const List: Components['List'] = forwardRef(({ style, children }, ref) => {
    return (
        <ol
            aria-label='Projects in workspace'
            ref={ref as LegacyRef<HTMLOListElement>}
            className={classes.projectListWrapper}
            style={style}
        >
            {children}
        </ol>
    );
});

type ListItemProps = ComponentType<
    Omit<UnwrapProps<Components['Item']>, 'item'> & {
        item: ProjectProps;
    }
>;

const ListItem: ListItemProps = ({ item, ...rest }) => {
    return (
        <li {...rest} key={item.id}>
            <Project project={item} />
        </li>
    );
};

const Footer: Components['Footer'] = () => {
    return (
        <View marginTop={'size-200'}>
            <ProjectListItemSkeletonLoader itemCount={1} />
        </View>
    );
};

export const ProjectsList = ({ projects, projectsQuery }: ProjectsListProps): JSX.Element => {
    useEffect(() => {
        // The user might have searched for a project (using our client side search) and
        // not found a project in the currently loaded pages.
        // In this case if there are more pages, then we want to load these before showing
        // a "Not Found" result
        if (isEmpty(projects) && projectsQuery.hasNextPage && !projectsQuery.isFetchingNextPage) {
            projectsQuery.fetchNextPage();
        }
    }, [projects, projectsQuery]);

    if (isEmpty(projects)) {
        if (projectsQuery.isFetchingNextPage) {
            return <LoadingOverlay visible />;
        }

        return <NotFound />;
    }

    return (
        <Virtuoso
            data={projects}
            components={{ List, Item: ListItem, Footer: projectsQuery.isFetchingNextPage ? Footer : undefined }}
            endReached={() => {
                if (projectsQuery.hasNextPage && !projectsQuery.isFetchingNextPage) {
                    projectsQuery.fetchNextPage();
                }
            }}
        />
    );
};
