// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';
import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';

import { AdvancedFilterOptions } from '../../../../core/media/media-filter.interface';
import { MediaAdvancedFilterResponse, MediaItemResponse } from '../../../../core/media/media.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
import { useFilterSearchParam } from '../../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { useSortingParams } from '../../../../hooks/use-sorting-params/use-sorting-params.hook';
import { useActiveMediaQuery } from '../../../media/hooks/media-items/active-media-query.hook';
import { useAdvancedFilterQuery } from '../../../media/hooks/media-items/advanced-filter-query.hook';
import { useDatasetIdentifier } from '../../hooks/use-dataset-identifier.hook';
import { useMediaFilterEmpty } from '../../hooks/use-media-filter-empty.hook';
import { useIsInActiveMode } from './use-is-in-active-mode.hook';

interface DatasetContextProps {
    datasetIdentifier: DatasetIdentifier;
    isInActiveMode: boolean;

    mediaItemsQuery: UseInfiniteQueryResult<InfiniteData<MediaItemResponse | MediaAdvancedFilterResponse>>;

    mediaFilterQuery: UseInfiniteQueryResult<InfiniteData<MediaAdvancedFilterResponse>>;
    mediaFilterOptions: AdvancedFilterOptions;
    setMediaFilterOptions: (rules: AdvancedFilterOptions) => void;
    isMediaFilterEmpty: boolean;

    activeMediaItemsQuery: UseInfiniteQueryResult<InfiniteData<MediaItemResponse>>;
    totalMatches: number;
    isMediaFetching: boolean;

    refetchMedia: () => Promise<void>;
}

const DatasetContext = createContext<DatasetContextProps | undefined>(undefined);

interface DatasetProviderProps {
    children: ReactNode;
}

export const DatasetProvider = ({ children }: DatasetProviderProps): JSX.Element => {
    const { mediaService } = useApplicationServices();
    const isInActiveMode = useIsInActiveMode();
    const { sortingOptions } = useSortingParams();
    const [mediaFilterOptions, setMediaFilterOptions] = useFilterSearchParam<AdvancedFilterOptions>(
        'filter',
        isInActiveMode
    );

    const datasetIdentifier = useDatasetIdentifier();
    const activeMediaItemsQuery = useActiveMediaQuery(mediaService, datasetIdentifier);
    const mediaFilterQuery = useAdvancedFilterQuery(
        mediaService,
        datasetIdentifier,
        {},
        100,
        mediaFilterOptions,
        sortingOptions
    );

    const isMediaFilterEmpty = useMediaFilterEmpty(mediaFilterOptions);

    const { totalMatchedImages = 0, totalMatchedVideos = 0 } = mediaFilterQuery.data?.pages[0] ?? {};

    const mediaItemsQuery = isInActiveMode ? activeMediaItemsQuery : mediaFilterQuery;

    const refetchMedia = async () => {
        await Promise.all([mediaFilterQuery.refetch(), activeMediaItemsQuery.refetch()]);
    };

    const value: DatasetContextProps = {
        mediaItemsQuery,
        mediaFilterQuery,
        mediaFilterOptions,
        isMediaFilterEmpty,
        setMediaFilterOptions,
        activeMediaItemsQuery,
        datasetIdentifier,
        isInActiveMode,
        refetchMedia,
        totalMatches: totalMatchedImages + totalMatchedVideos,
        isMediaFetching: mediaFilterQuery.isFetching,
    };

    return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>;
};

export const useDataset = (): DatasetContextProps => {
    const context = useContext(DatasetContext);

    if (context === undefined) {
        throw new MissingProviderError('useDataset', 'DatasetProvider');
    }

    return context;
};
