// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, ReactNode } from 'react';

export interface MenuTriggerProps {
    id: string;
    items: string[];
    menuTooltip?: ReactNode;
    disabledKeys?: Key[];
    onAction: (key: Key) => void;
    selectedKey?: Iterable<string>;
    onOpenChange?: (isOpen: boolean) => void;
    renderContent?: (item: string) => JSX.Element;
    children: JSX.Element;
    ariaLabel?: string;
}

export enum MenuItemsKey {
    FILES = 'Files',
    FOLDER = 'Folder',
    CAMERA = 'Camera',
    FILE = 'File',
}
