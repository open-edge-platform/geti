// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, SetStateAction, useState } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';

import { ProjectSortingOptions, ProjectsQueryOptions } from '../../../core/projects/services/project-service.interface';
import { useDebouncedCallback } from '../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { HasPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
import { SearchField } from '../../../shared/components/search-field/search-field.component';
import { NewProjectDialog } from '../../create-project/new-project-dialog.component';
import { ProjectSorting } from './components/project-sorting/project-sorting.component';

import sharedClasses from '../../../shared/shared.module.scss';

interface ProjectActionsProps {
    // We want to show search field in two cases:
    // 1. We have at least one project.
    // 2. We filtered projects by name and we don't have any projects on the list.
    shouldShowProjectActions: boolean;

    queryOptions: ProjectsQueryOptions;
    setQueryOptions: Dispatch<SetStateAction<ProjectsQueryOptions>>;

    datasetImportDialogTrigger: OverlayTriggerState;
}

export const ProjectsActions = ({
    queryOptions,
    setQueryOptions,
    shouldShowProjectActions,
    datasetImportDialogTrigger,
}: ProjectActionsProps): JSX.Element => {
    const [filterText, setFilterText] = useState<string>('');

    const handleQueryOptions = useDebouncedCallback((projectName: string) => {
        setQueryOptions((prevQueryOptions) => {
            const newQueryOptions: ProjectsQueryOptions = { ...prevQueryOptions, name: projectName };

            if (newQueryOptions.name === '') {
                delete newQueryOptions.name;
            }

            return newQueryOptions;
        });
    }, 300);

    const handleFilterTextChange = (value: string) => {
        setFilterText(value);

        handleQueryOptions(value);
    };

    return (
        <Flex marginY='size-200' width={'100%'} gap='size-150' alignItems={'center'} justifyContent={'end'}>
            <Flex gap={'size-100'}>
                {shouldShowProjectActions && (
                    <>
                        <SearchField
                            isQuiet
                            value={filterText}
                            onChange={handleFilterTextChange}
                            aria-label={'Search...'}
                            id={'list-search-field'}
                            UNSAFE_className={`${sharedClasses.searchField} ${
                                filterText.length ? sharedClasses.searchFieldOpen : ''
                            }`}
                            placeholder='Search by name'
                        />

                        <ProjectSorting
                            nameKey={ProjectSortingOptions.name}
                            dateKey={ProjectSortingOptions.creationDate}
                            sortingOptions={queryOptions}
                            setSortingOptions={setQueryOptions}
                        />
                    </>
                )}
                <HasPermission operations={[OPERATION.PROJECT_CREATION]}>
                    <NewProjectDialog
                        buttonText={'Create new project'}
                        openImportDatasetDialog={datasetImportDialogTrigger}
                    />
                </HasPermission>
            </Flex>
        </Flex>
    );
};
