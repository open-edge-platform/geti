// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
