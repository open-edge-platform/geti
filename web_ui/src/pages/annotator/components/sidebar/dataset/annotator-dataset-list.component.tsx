// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
