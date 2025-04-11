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

import { usePrevious } from '../../../../../hooks/use-previous/use-previous.hook';
import { ViewModes } from '../../../../../shared/components/media-view-modes/utils';
import { useDataset } from '../../../providers/dataset-provider/dataset-provider.component';
import { useSelectedMediaItem } from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useSelectMediaItemWithSaveConfirmation } from '../../../providers/submit-annotations-provider/use-select-media-item-with-save-confirmation.hook';
import { DatasetList } from './dataset-list.component';

interface AnnotatorDatasetListProps {
    viewMode: ViewModes;
}

export const AnnotatorDatasetList = ({ viewMode }: AnnotatorDatasetListProps): JSX.Element => {
    const { selectedMediaItem, setSelectedMediaItem } = useSelectedMediaItem();
    const previouslySelectedMediaItem = usePrevious(selectedMediaItem);
    const selectWithSavingConfirmation = useSelectMediaItemWithSaveConfirmation(setSelectedMediaItem);

    const { isInActiveMode, mediaItemsQuery, isMediaFilterEmpty } = useDataset();

    return (
        <DatasetList
            previouslySelectedMediaItem={previouslySelectedMediaItem}
            selectedMediaItem={selectedMediaItem}
            selectMediaItem={selectWithSavingConfirmation}
            mediaItemsQuery={mediaItemsQuery}
            isInActiveMode={isInActiveMode}
            isMediaFilterEmpty={isMediaFilterEmpty}
            shouldShowAnnotationIndicator
            viewMode={viewMode}
            isReadOnly={false}
        />
    );
};
