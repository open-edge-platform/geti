// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, Dispatch, SetStateAction } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { Accordion } from '@shared/components/accordion/accordion.component';
import { MediaViewModes } from '@shared/components/media-view-modes/media-view-modes.component';
import { ViewModes } from '@shared/components/media-view-modes/utils';
import { RefreshButton } from '@shared/components/refresh-button/refresh-button.component';
import { TutorialCardBuilder } from '@shared/components/tutorial-card/tutorial-card-builder.component';
import { useQueryClient } from '@tanstack/react-query';

import { isAnomalyDomain } from '../../../../../core/projects/domains';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
import { TUTORIAL_CARD_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { useSortingParams } from '../../../../../hooks/use-sorting-params/use-sorting-params.hook';
import { MediaFilterChips } from '../../../../media/components/media-filter-chips.component';
import { MediaSearch } from '../../../../media/media-actions/media-search.component';
import { MediaSorting } from '../../../../media/media-actions/media-sorting.component';
import { MediaFilter } from '../../../../media/media-filter.component';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { useIsSceneBusy } from '../../../hooks/use-annotator-scene-interaction-state.hook';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { useDataset } from '../../../providers/dataset-provider/dataset-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { ActiveDatasetTooltipComponent } from './active-dataset-tooltip.component';
import { AnnotatorDatasetList } from './annotator-dataset-list.component';
import { DatasetPicker } from './dataset-picker/dataset-picker.component';

const DATASET_ANNOTATOR_THEME = {
    '--detailsBackground': 'var(--spectrum-global-color-gray-300)',
    '--detailsDividerBackground': 'var(--spectrum-global-color-gray-50)',
} as CSSProperties;

interface DatasetAccordionProps {
    viewMode: ViewModes;
    setViewMode: Dispatch<SetStateAction<ViewModes>>;
}

const RefreshActiveSet = () => {
    const { activeMediaItemsQuery } = useDataset();
    const { selectedTask } = useTask();
    const datasetIdentifier = useDatasetIdentifier();
    const queryClient = useQueryClient();

    const isFetching = activeMediaItemsQuery.isFetching || activeMediaItemsQuery.isFetchingNextPage;
    const mediaCount = activeMediaItemsQuery?.data?.pages.flatMap(({ media }) => media).length || 0;

    const refresh = () => {
        // Remove old pages, then refetch the first page
        queryClient.removeQueries({ queryKey: QUERY_KEYS.ACTIVE_MEDIA_ITEMS(datasetIdentifier, selectedTask) });
        activeMediaItemsQuery.refetch();
    };

    return (
        <>
            <ActiveDatasetTooltipComponent count={mediaCount} />
            <RefreshButton
                id='refresh-active-set'
                ariaLabel='Refresh active set'
                onPress={refresh}
                isLoading={isFetching}
                tooltip='Refresh active set'
            />
        </>
    );
};

export const DatasetAccordion = ({ setViewMode, viewMode }: DatasetAccordionProps): JSX.Element => {
    const {
        totalMatches,
        isInActiveMode,
        isMediaFetching,
        mediaFilterOptions,
        isMediaFilterEmpty,
        setMediaFilterOptions,
    } = useDataset();

    const {
        project: { labels },
        isSingleDomainProject,
    } = useProject();

    const isSceneBusy = useIsSceneBusy();
    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);
    const { sortingOptions, setSortingOptions } = useSortingParams();

    return (
        <Accordion
            defaultOpenState
            height='100%'
            overflow='auto'
            padding='size-100'
            idPrefix='active-set'
            hasFoldButton={false}
            header={
                <Flex justifyContent='space-between' flexGrow={1} alignItems='center'>
                    <View
                        id='dataset-picker-id'
                        marginY='size-150'
                        borderBottomColor='gray-400'
                        borderBottomWidth='thin'
                    >
                        <DatasetPicker />
                    </View>
                    <Flex>
                        <MediaSearch
                            setMediaFilterOptions={setMediaFilterOptions}
                            mediaFilterOptions={mediaFilterOptions}
                        />

                        {!isInActiveMode && (
                            <MediaSorting sortingOptions={sortingOptions} setSortingOptions={setSortingOptions} />
                        )}

                        {isInActiveMode && <RefreshActiveSet />}
                        {!isInActiveMode && (
                            <MediaFilter
                                isDatasetAccordion
                                isDisabled={isSceneBusy}
                                totalMatches={totalMatches}
                                isMediaFetching={isMediaFetching}
                                filterOptions={mediaFilterOptions}
                                isMediaFilterEmpty={isMediaFilterEmpty}
                                onSetFilterOptions={setMediaFilterOptions}
                            />
                        )}
                        <MediaViewModes viewMode={viewMode} setViewMode={setViewMode} />
                    </Flex>
                </Flex>
            }
        >
            <Flex
                direction='column'
                height='100%'
                minHeight={0}
                UNSAFE_style={DATASET_ANNOTATOR_THEME}
                gap={'size-100'}
            >
                <TutorialCardBuilder
                    cardKey={TUTORIAL_CARD_KEYS.ANNOTATOR_DATASET_TUTORIAL}
                    styles={{ fontSize: 'var(--spectrum-global-dimension-font-size-50)' }}
                />
                {!isInActiveMode && (
                    <MediaFilterChips
                        labels={labels}
                        isAnomalyProject={isAnomalyProject}
                        mediaFilterOptions={mediaFilterOptions}
                        setMediaFilterOptions={setMediaFilterOptions}
                        darkMode
                    />
                )}

                <AnnotatorDatasetList viewMode={viewMode} />
            </Flex>
        </Accordion>
    );
};
