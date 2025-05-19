// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SpectrumDropZoneProps as DropZoneProps, DropZone as SpectrumDropZone } from '@geti/ui';
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
