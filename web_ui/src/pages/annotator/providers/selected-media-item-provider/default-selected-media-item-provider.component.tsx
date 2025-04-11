// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import noop from 'lodash/noop';

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
