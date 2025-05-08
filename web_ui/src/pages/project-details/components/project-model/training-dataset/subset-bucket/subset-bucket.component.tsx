// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, useMemo, useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { capitalize } from 'lodash-es';

import { BulbIcon, DocumentIcon, ShieldFilled } from '../../../../../../assets/icons';
import { useTrainingDatasetMediaQuery } from '../../../../../../core/datasets/hooks/use-training-dataset.hook';
import {
    AdvancedFilterOptions,
    AdvancedFilterSortingOptions,
    SearchRuleField,
} from '../../../../../../core/media/media-filter.interface';
import { MediaItem } from '../../../../../../core/media/media.interface';
import { ProjectIdentifier } from '../../../../../../core/projects/core.interface';
import { useFilterSearchParam } from '../../../../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { useViewMode } from '../../../../../../hooks/use-view-mode/use-view-mode.hook';
import { MediaViewModes } from '../../../../../../shared/components/media-view-modes/media-view-modes.component';
import { ViewModes } from '../../../../../../shared/components/media-view-modes/utils';
import { DatasetList } from '../../../../../annotator/components/sidebar/dataset/dataset-list.component';
import { useMediaFilterEmpty } from '../../../../../annotator/hooks/use-media-filter-empty.hook';
import { TaskProvider } from '../../../../../annotator/providers/task-provider/task-provider.component';
import { MediaFilterChips } from '../../../../../media/components/media-filter-chips.component';
import { MediaSearch } from '../../../../../media/media-actions/media-search.component';
import { MediaSorting } from '../../../../../media/media-actions/media-sorting.component';
import { MediaFilter } from '../../../../../media/media-filter.component';
import { mergeMediaFilters } from '../../../../../media/providers/utils';
import { MediaItemTooltipMessage } from '../../../project-media/media-item-tooltip-message/media-item-tooltip-message';
import { getMediaItemTooltipProps } from '../../../project-media/media-item-tooltip-message/utils';
import { TrainingDatasetDetailsPreview } from '../training-dataset-details-preview/training-dataset-details-preview.component';
import { TrainingDatasetProps } from '../training-dataset.interface';
import { getSubsetMediaFilter, Subset } from '../utils';

interface SubsetBucketProps extends TrainingDatasetProps {
    mediaPercentage: string;
    projectIdentifier: ProjectIdentifier;
    type: Subset;
}

const DATASET_MODEL_THEME = {
    '--detailsBackground': 'var(--spectrum-global-color-gray-75)',
    '--detailsDividerBackground': 'var(--spectrum-global-color-gray-300)',
} as CSSProperties;

export const SubsetBucket = ({
    mediaPercentage,
    projectIdentifier,
    storageId,
    revisionId,
    type,
    modelLabels,
    modelInformation,
    taskId,
    isActive,
}: SubsetBucketProps): JSX.Element => {
    const [mediaFilterOptions, setMediaFilterOptions] = useFilterSearchParam<AdvancedFilterOptions>(`filter-${type}`);
    const [sortingOptions, setSortingOptions] = useState<AdvancedFilterSortingOptions>({});
    const [viewMode, setViewMode] = useViewMode(type, ViewModes.SMALL);

    const title = capitalize(type);

    const [selectedMediaItem, setSelectedMediaItem] = useState<MediaItem>();

    const Icon = type === Subset.TESTING ? BulbIcon : type === Subset.VALIDATION ? DocumentIcon : ShieldFilled;

    const searchOptions = useMemo(
        () => mergeMediaFilters(getSubsetMediaFilter(type), mediaFilterOptions),
        [type, mediaFilterOptions]
    );

    const subsetMediaItemsQuery = useTrainingDatasetMediaQuery(
        projectIdentifier,
        storageId,
        revisionId,
        searchOptions,
        sortingOptions
    );

    const isMediaFilterEmpty = useMediaFilterEmpty(mediaFilterOptions);

    const { totalMatchedImages = 0, totalMatchedVideos = 0 } = subsetMediaItemsQuery.data?.pages[0] ?? {};

    const getItemTooltip = (item: MediaItem): JSX.Element => {
        const tooltipProps = getMediaItemTooltipProps(item);

        return <MediaItemTooltipMessage {...tooltipProps} />;
    };

    return (
        <Flex id={`${type}-subset`} flexGrow={1} direction={'column'} data-testid={`${type}-subset`}>
            <Flex
                gap={'size-100'}
                alignItems={'center'}
                marginBottom={'size-100'}
                data-testid={`${type}-subset-title`}
                id={`${type}-subset-title`}
                UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-font-size-200)' }}
            >
                <Icon />
                <span>{title}</span>
                <span>{mediaPercentage}</span>
            </Flex>
            <View
                height={'96%'}
                padding={'size-200'}
                borderWidth={'thin'}
                borderColor={'gray-400'}
                borderRadius={'regular'}
                backgroundColor={'gray-50'}
                UNSAFE_style={{ display: 'flex', flexDirection: 'column' }}
            >
                <Flex justifyContent={'end'}>
                    <MediaSearch
                        mediaFilterOptions={mediaFilterOptions}
                        setMediaFilterOptions={setMediaFilterOptions}
                        id={type}
                    />
                    <MediaFilter
                        totalMatches={totalMatchedImages + totalMatchedVideos}
                        isMediaFetching={subsetMediaItemsQuery.isFetching}
                        filterOptions={mediaFilterOptions}
                        isMediaFilterEmpty={isMediaFilterEmpty}
                        onSetFilterOptions={setMediaFilterOptions}
                        id={type}
                        disabledFilterRules={[SearchRuleField.AnnotationSceneState]}
                    />
                    <MediaViewModes viewMode={viewMode} setViewMode={setViewMode} />
                    <MediaSorting setSortingOptions={setSortingOptions} sortingOptions={sortingOptions} />
                </Flex>

                <Flex
                    height='100%'
                    minHeight={0}
                    direction='column'
                    gap={'size-100'}
                    UNSAFE_style={DATASET_MODEL_THEME}
                >
                    <MediaFilterChips
                        labels={modelLabels}
                        isAnomalyProject={false}
                        mediaFilterOptions={mediaFilterOptions}
                        setMediaFilterOptions={setMediaFilterOptions}
                        id={type}
                    />
                    <DatasetList
                        isReadOnly
                        viewMode={viewMode}
                        getItemTooltip={getItemTooltip}
                        selectMediaItem={setSelectedMediaItem}
                        mediaItemsQuery={subsetMediaItemsQuery}
                        shouldShowAnnotationIndicator={false}
                    />
                </Flex>

                <TaskProvider>
                    {selectedMediaItem && (
                        <TrainingDatasetDetailsPreview
                            selectedMediaItem={selectedMediaItem}
                            setSelectedMediaItem={setSelectedMediaItem}
                            datasetIdentifier={{ ...projectIdentifier, datasetId: storageId }}
                            coreLabels={modelLabels}
                            searchOptions={searchOptions}
                            sortingOptions={sortingOptions}
                            revisionId={revisionId}
                            taskId={taskId}
                            isActive={isActive}
                            modelInformation={modelInformation}
                            title={`${title} subset`}
                            mediaItemsQuery={subsetMediaItemsQuery}
                        />
                    )}
                </TaskProvider>
            </View>
        </Flex>
    );
};
