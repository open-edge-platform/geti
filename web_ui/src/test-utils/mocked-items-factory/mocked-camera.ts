// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import { Screenshot } from '../../pages/camera-support/camera.interface';
import { mockFile } from '../mockFile';

export const getMockedScreenshot = ({
    fileName,
    lastModified,
    ...props
}: Partial<Screenshot> & { fileName?: string; lastModified?: number }) => {
    const file = mockFile({ type: MEDIA_TYPE.IMAGE, name: fileName, lastModified });

    return {
        id: 'id-test',
        dataUrl: 'data-url-test',
        labelIds: [],
        file,
        labelName: null,
        ...props,
    };
};
