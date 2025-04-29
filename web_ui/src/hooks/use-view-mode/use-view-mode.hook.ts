// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useLocalStorage } from 'usehooks-ts';

import { Subset } from '../../pages/project-details/components/project-model/training-dataset/utils';
import { MediaItemsBucketType } from '../../pages/project-details/components/project-test/media-items-bucket.interface';
import { MEDIA_CONTENT_BUCKET } from '../../providers/media-upload-provider/media-upload.interface';
import { INITIAL_VIEW_MODE } from '../../shared/components/media-view-modes/utils';
import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';

type BucketType = MEDIA_CONTENT_BUCKET | Subset | MediaItemsBucketType;

const getMediaViewModeKey = (bucket: BucketType) => {
    return `${LOCAL_STORAGE_KEYS.MEDIA_VIEW_MODE}-${bucket.toString()}`;
};

export const useViewMode = (type: BucketType, defaultViewMode = INITIAL_VIEW_MODE) => {
    return useLocalStorage(getMediaViewModeKey(type), defaultViewMode);
};
