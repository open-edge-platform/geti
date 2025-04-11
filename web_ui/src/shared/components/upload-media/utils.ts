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

import { Key, MutableRefObject } from 'react';

import { MenuItemsKey } from './upload-media-button/upload-media-button.interface';

export const DIRECTORY_ATTRS = ['allowdirs', 'directory', 'mozdirectory', 'webkitdirectory'];

export const onMenuAction = async (key: Key, fileInputRef: MutableRefObject<HTMLInputElement>): Promise<void> => {
    switch (key) {
        case MenuItemsKey.FILE.toLowerCase():
        case MenuItemsKey.FILES.toLowerCase():
            for (const attr of DIRECTORY_ATTRS) {
                fileInputRef.current.removeAttribute(attr);
            }

            break;
        case MenuItemsKey.FOLDER.toLowerCase():
            for (const attr of DIRECTORY_ATTRS) {
                fileInputRef.current.setAttribute(attr, '');
            }

            break;
    }

    fileInputRef.current.click();
};
