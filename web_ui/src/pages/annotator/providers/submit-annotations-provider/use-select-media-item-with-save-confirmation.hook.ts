// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback } from 'react';

import { MediaItem } from '../../../../core/media/media.interface';
import { useSubmitAnnotations } from './submit-annotations-provider.component';

export const useSelectMediaItemWithSaveConfirmation = (
    setSelectedMediaItem: (media: MediaItem) => void
): ((mediaItem: MediaItem) => Promise<void>) => {
    const { confirmSaveAnnotations } = useSubmitAnnotations();

    const selectWithSavingConfirmation = useCallback(
        (mediaItem: MediaItem) => {
            return confirmSaveAnnotations(async () => {
                setSelectedMediaItem(mediaItem);
            });
        },
        [confirmSaveAnnotations, setSelectedMediaItem]
    );

    return selectWithSavingConfirmation;
};
