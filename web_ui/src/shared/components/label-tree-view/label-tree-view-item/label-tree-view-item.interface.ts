// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../../../core/projects/core.interface';

interface TreeViewItemCommonProps<T> {
    item: T;
    savedItem: T;
    save: (newItem: T) => void;
    newTree: boolean;
}

export interface TreeViewItemContentProps {
    onOpenClickHandler: () => void;
    isOpen: boolean;
    inEditionMode: boolean;
}

export interface TreeViewItemEditModeProps<T> extends TreeViewItemCommonProps<T> {
    flatListProjectItems: T[];
    domains: DOMAIN[];
    setValidationError: (id: string, validationErrors: Record<string, string>) => void;
    validationErrors: Record<string, string>;
}
