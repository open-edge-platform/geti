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

import { Cell, Column, Row, TableBody, TableHeader, TableView, Text } from '@adobe/react-spectrum';
import capitalize from 'lodash/capitalize';

import { ProjectProps } from '../../../../core/projects/project.interface';
import {
    ProjectSortingOptions,
    ProjectsQueryOptions,
} from '../../../../core/projects/services/project-service.interface';
import { paths } from '../../../../core/services/routes';
import { useFirstWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { TruncatedText } from '../../../../shared/components/truncated-text/truncated-text.component';
import { getFileSize, SpectrumTableLoadingState } from '../../../../shared/utils';
import { ProjectActionCell } from './project-action-cell.component';

enum ProjectsColumns {
    NAME = 'name',
    SIZE = 'size',
    ACTION = 'action',
}

const ProjectNameCell = ({ name }: { name: string }): JSX.Element => {
    return <TruncatedText>{name}</TruncatedText>;
};

const ProjectSizeCell = ({ size }: { size: number }): JSX.Element => {
    return <Text>{getFileSize(size)}</Text>;
};

const COLUMNS = [
    {
        name: ProjectsColumns.NAME,
        isSortable: true,
    },
    {
        name: ProjectsColumns.SIZE,
        isSortable: false,
    },
    {
        name: ProjectsColumns.ACTION,
        isSortable: false,
    },
];

interface ProjectStorageTableProps {
    projects: ProjectProps[];
    isInitialLoading: boolean;
    isFetchingNextPage: boolean;
    queryOptions: ProjectsQueryOptions;
    onSortChange: (props: ProjectsQueryOptions) => void;
    onLoadMore: () => void;
}

export const ProjectStorageTable = ({
    projects,
    isInitialLoading,
    isFetchingNextPage,
    queryOptions,
    onSortChange,
    onLoadMore,
}: ProjectStorageTableProps): JSX.Element => {
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();

    return (
        <TableView
            aria-label={'Projects storage table'}
            onSortChange={(change) => {
                onSortChange({
                    sortBy: change.column as ProjectSortingOptions,
                    sortDir: change.direction === 'ascending' ? 'asc' : 'dsc',
                });
            }}
            sortDescriptor={{
                column: queryOptions.sortBy,
                direction: queryOptions.sortDir === 'asc' ? 'ascending' : 'descending',
            }}
            minHeight={'size-2400'}
            height={'100%'}
        >
            <TableHeader columns={COLUMNS}>
                {({ name, isSortable }) => (
                    <Column key={name} allowsSorting={isSortable} hideHeader={name === ProjectsColumns.ACTION}>
                        {capitalize(name)}
                    </Column>
                )}
            </TableHeader>
            <TableBody
                items={projects}
                onLoadMore={onLoadMore}
                loadingState={
                    isInitialLoading
                        ? SpectrumTableLoadingState.loading
                        : isFetchingNextPage
                          ? SpectrumTableLoadingState.loadingMore
                          : undefined
                }
            >
                {(project) => {
                    return (
                        <Row
                            key={project.id}
                            href={paths.project.index({ organizationId, workspaceId, projectId: project.id })}
                            routerOptions={{ viewTransition: true }}
                        >
                            <Cell>
                                <ProjectNameCell name={project.name} />
                            </Cell>
                            <Cell>
                                <ProjectSizeCell size={project.storageInfo.size} />
                            </Cell>
                            <Cell>
                                <ProjectActionCell name={project.name} id={project.id} />
                            </Cell>
                        </Row>
                    );
                }}
            </TableBody>
        </TableView>
    );
};
