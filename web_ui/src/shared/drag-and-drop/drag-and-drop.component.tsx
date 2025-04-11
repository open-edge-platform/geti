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

import { SpectrumDropZoneProps as DropZoneProps, DropZone as SpectrumDropZone } from '@adobe/react-spectrum';
import clsx from 'clsx';

import { GetElementType } from '../utils';

import classes from './drag-and-drop.module.scss';

type DropItem = GetElementType<DropEvent['items']>;
type DropEvent = Parameters<NonNullable<DropZoneProps['onDrop']>>[0];

const toArray = async <T,>(asyncIterator: AsyncIterable<T>) => {
    const arr = [];
    for await (const i of asyncIterator) arr.push(i);
    return arr;
};

async function flattenDropItemToFiles(item: DropItem): Promise<File[]> {
    if (item.kind === 'file') {
        const file = await item.getFile();

        return [file];
    }

    if (item.kind === 'text') {
        return [];
    }

    const entries = await toArray(item.getEntries());

    const filesFromDirectory = [];
    for await (const entry of entries) {
        if (entry.kind === 'directory') {
            filesFromDirectory.push(...(await flattenDropItemToFiles(entry)));
        } else {
            filesFromDirectory.push(await entry.getFile());
        }
    }

    return filesFromDirectory;
}

async function getFilesFromDropEvent(e: DropEvent): Promise<File[]> {
    const files: File[] = [];
    for await (const item of e.items) {
        files.push(...(await flattenDropItemToFiles(item)));
    }

    return files;
}

export const onDropFiles = (handleFiles: (files: File[]) => void): DropZoneProps['onDrop'] => {
    return async (event) => {
        const files = await getFilesFromDropEvent(event);

        return handleFiles(files);
    };
};

export const DropZone = (props: DropZoneProps & { background?: boolean }) => {
    const { background, UNSAFE_style, UNSAFE_className, ...rest } = props;
    const backgroundColor = background ? 'var(--spectrum-global-color-gray-100)' : 'transparent';

    return (
        <SpectrumDropZone
            UNSAFE_className={clsx(classes.dragAndDrop, UNSAFE_className)}
            UNSAFE_style={{ backgroundColor, ...UNSAFE_style }}
            margin={0}
            {...rest}
        />
    );
};
