// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentType, forwardRef, LegacyRef, useEffect } from 'react';

import { View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
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
