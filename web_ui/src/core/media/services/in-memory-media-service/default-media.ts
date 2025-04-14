// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { MEDIA_TYPE } from '../../base-media.interface';
import { MEDIA_ANNOTATION_STATUS } from '../../base.interface';
import { MediaItem } from '../../media.interface';
import Antelope from './../../../../assets/tests-assets/antelope.webp';
import Thumb7 from './../../../../assets/tests-assets/spade-ace.webp';
import Thumb1 from './../../../../assets/tests-assets/thumb-1.webp';
import Thumb2 from './../../../../assets/tests-assets/thumb-2.webp';
import Thumb3 from './../../../../assets/tests-assets/thumb-3.webp';
import Thumb4 from './../../../../assets/tests-assets/thumb-4.webp';
import Thumb5 from './../../../../assets/tests-assets/thumb-5.webp';
import Thumb6 from './../../../../assets/tests-assets/thumb-6.webp';

export const DEFAULT_IN_MEMORY_MEDIA: MediaItem[] = [
    getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: '1' },
        thumbnailSrc: Thumb1,
        src: Thumb1,
        name: 'Antelope 1',
    }),
    getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: '2' },
        thumbnailSrc: Thumb2,
        src: Thumb2,
        name: 'Antelope 2',
        status: MEDIA_ANNOTATION_STATUS.ANNOTATED,
    }),
    getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: '3' },
        thumbnailSrc: Thumb3,
        src: Antelope,
        name: 'Antelope 3',
        status: MEDIA_ANNOTATION_STATUS.ANNOTATED,
    }),
    getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: '4' },
        thumbnailSrc: Thumb4,
        src: Thumb4,
        name: 'Antelope 4',
    }),
    getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: '5' },
        thumbnailSrc: Thumb5,
        src: Thumb5,
        name: 'Antelope 5',
    }),
    getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: '6' },
        thumbnailSrc: Thumb6,
        src: Thumb6,
        name: 'Antelope 6',
        status: MEDIA_ANNOTATION_STATUS.ANNOTATED,
    }),
    getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: '7' },
        thumbnailSrc: Thumb7,
        src: Thumb7,
        name: 'Spade ace',
        status: MEDIA_ANNOTATION_STATUS.ANNOTATED,
    }),
];
