// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
