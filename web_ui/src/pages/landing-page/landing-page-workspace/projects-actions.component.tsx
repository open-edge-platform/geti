// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useState } from 'react';

import { Flex, SearchField } from '@geti/ui';
import { OverlayTriggerState } from '@react-stately/overlays';

import { ProjectSortingOptions, ProjectsQueryOptions } from '../../../core/projects/services/project-service.interface';
import { useDebouncedCallback } from '../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { HasPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
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
