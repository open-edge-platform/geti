// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { noop } from 'lodash-es';

import { PredictionResult } from '../../../../core/annotations/services/prediction-service.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { SelectedMediaItemContext, SelectedMediaItemProps } from './selected-media-item-provider.component';
import { SelectedMediaItem } from './selected-media-item.interface';

interface SelectedMediaItemProviderProps {
    children: ReactNode;
    selectedMediaItem?: SelectedMediaItem;
}

export const DefaultSelectedMediaItemProvider = ({
    children,
    selectedMediaItem,
}: SelectedMediaItemProviderProps): JSX.Element => {
    // This is an artificial query: we already have the selected media item,
    // so we don't need to query it, however some annotator components rely
    // on reading this query's (loading, success etc) status
    const selectedMediaItemQuery = useQuery({
        queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.DEFAULT(selectedMediaItem?.identifier),
        queryFn: async () => {
            if (selectedMediaItem === undefined) {
                throw new Error("Can't fetch undefined media item");
            }

            return selectedMediaItem;
        },
        enabled: selectedMediaItem !== undefined,
    });

    const value: SelectedMediaItemProps = {
        selectedMediaItem,
        selectedMediaItemQuery,
        setSelectedMediaItem: noop,
        predictionsQuery: { isLoading: false } as UseQueryResult<PredictionResult>,
    };

    return <SelectedMediaItemContext.Provider value={value}>{children}</SelectedMediaItemContext.Provider>;
};
