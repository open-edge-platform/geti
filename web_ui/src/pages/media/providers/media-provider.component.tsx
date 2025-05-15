// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useCallback, useContext, useState } from 'react';

import { InfiniteData } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { AdvancedFilterOptions } from '../../../core/media/media-filter.interface';
import { MediaAdvancedCount, MediaAdvancedFilterResponse, MediaItem } from '../../../core/media/media.interface';
import { useApplicationServices } from '../../../core/services/application-services-provider.component';
import { useFilterSearchParam } from '../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { useSortingParams } from '../../../hooks/use-sorting-params/use-sorting-params.hook';
import { MissingProviderError } from '../../../shared/missing-provider-error';
import { useDatasetIdentifier } from '../../annotator/hooks/use-dataset-identifier.hook';
import { useDeleteMediaMutation } from '../hooks/media-delete/media-delete.hook';
import { useAdvancedMediaFilter } from '../hooks/media-items/advanced-media-filter.hook';
import { mergeMediaFilters } from './utils';

const MEDIA_ITEMS_DEFAULT_LOAD_SIZE = 100;

interface MediaContextProps extends MediaAdvancedCount {
    readonly media: MediaItem[];
    readonly mediaSelection: MediaItem[];
    readonly mediaItemsLoadSize: number;
    readonly isMediaFetching: boolean;
    readonly isDeletionInProgress: boolean;
    readonly isMediaFilterEmpty: boolean;
    readonly isFetchingNextPage: boolean;
    readonly isLoading: boolean;
    readonly mediaFilterOptions: AdvancedFilterOptions;
    resetMediaSelection: () => void;
    loadNextMedia: (init?: boolean) => Promise<void>;
    deleteMedia: ReturnType<typeof useDeleteMediaMutation>['deleteMedia'];
    toggleItemInMediaSelection: (mediaItem: MediaItem) => void;
    addBulkMediaToSelection: (mediaItems: MediaItem[]) => void;
    setMediaItemsLoadSize: (size: number) => void;
    setMediaFilterOptions: (options: AdvancedFilterOptions) => void;
}

interface MediaProviderProps {
    requiredFilters?: AdvancedFilterOptions;
    filterName?: string;
    children: ReactNode;
}

const MediaContext = createContext<MediaContextProps | undefined>(undefined);

/*
    We use required filters for anomaly project to set filtering by labelId by default.
    We do not want to make lower components (e.g. MediaFilter) to be aware of required filters (we do not want to
    display them in the dialog). That's why we use them only in the request.
 */
export const MediaProvider = ({
    children,
    filterName = 'filter',
    requiredFilters = {},
}: MediaProviderProps): JSX.Element => {
    const { sortingOptions } = useSortingParams();
    const datasetIdentifier = useDatasetIdentifier();
    const { mediaService } = useApplicationServices();
    const [mediaSelection, setMediaSelection] = useState<MediaItem[]>([]);
    const [mediaItemsLoadSize, setMediaItemsLoadSize] = useState<number>(MEDIA_ITEMS_DEFAULT_LOAD_SIZE);
    const [mediaFilterOptions, setMediaFilterOptions] = useFilterSearchParam<AdvancedFilterOptions>(filterName);

    const {
        media,
        isLoading,
        isMediaFetching,
        loadNextMedia,
        isFetchingNextPage,
        totalImages,
        totalVideos,
        totalMatchedImages,
        totalMatchedVideos,
        totalMatchedVideoFrames,
    } = useAdvancedMediaFilter({
        mediaService,
        datasetIdentifier,
        queryOptions: {},
        sortingOptions,
        mediaItemsLoadSize,
        mediaFilterOptions: mergeMediaFilters(mediaFilterOptions, requiredFilters),
        onSuccess: ({ pages }: InfiniteData<MediaAdvancedFilterResponse>) => {
            // Reset media selection if we did not fetch a next page (i.e. refetched the query)
            if (pages.length === 1) resetMediaSelection();
        },
    });

    const { deleteMedia } = useDeleteMediaMutation();

    const isMediaFilterEmpty = isEmpty(mediaFilterOptions);

    const resetMediaSelection = () => {
        setMediaSelection([]);
    };

    const addBulkMediaToSelection = (selectedMediaItems: MediaItem[]): void => {
        setMediaSelection(selectedMediaItems);
    };

    const toggleItemInMediaSelection = useCallback(
        (mediaItem: MediaItem): void => {
            const newSelection = mediaSelection.filter(
                (selectionItem: MediaItem) => selectionItem.thumbnailSrc !== mediaItem.thumbnailSrc
            );

            if (newSelection.length < mediaSelection.length) {
                setMediaSelection(newSelection);

                return;
            }

            setMediaSelection((previousMediaSelection: MediaItem[]) => [...previousMediaSelection, mediaItem]);
        },
        [mediaSelection]
    );

    const value: MediaContextProps = {
        media,
        isLoading,
        totalImages,
        totalVideos,
        totalMatchedImages,
        totalMatchedVideos,
        totalMatchedVideoFrames,
        mediaSelection,
        mediaItemsLoadSize,
        isMediaFetching,
        isDeletionInProgress: deleteMedia.isPending,
        isMediaFilterEmpty,
        setMediaItemsLoadSize,
        loadNextMedia,
        isFetchingNextPage,
        deleteMedia,
        resetMediaSelection,
        addBulkMediaToSelection,
        toggleItemInMediaSelection,
        mediaFilterOptions,
        setMediaFilterOptions,
    };

    return <MediaContext.Provider value={value}>{children}</MediaContext.Provider>;
};

export const useMedia = (): MediaContextProps => {
    const context = useContext(MediaContext);

    if (context === undefined) {
        throw new MissingProviderError('useMedia', 'MediaProvider');
    }

    return context;
};
