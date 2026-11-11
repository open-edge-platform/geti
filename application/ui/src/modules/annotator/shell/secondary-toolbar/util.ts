// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Label } from '@/api/types';

import type { AnnotationLabelRef } from '../../../../shared/types';

export const toggleLabel = (newLabel: Label, labels: AnnotationLabelRef[]): AnnotationLabelRef[] => {
    const isExistingLabel = labels.some(({ id }) => id === newLabel.id);

    if (isExistingLabel) {
        return labels.filter(({ id }) => id !== newLabel.id);
    }

    return [...labels, { id: newLabel.id }];
};

export const getItemAfterDeletion = <T extends { id: string }>(items: T[], deletedId: string): T | undefined => {
    const deletedIndex = items.findIndex(({ id }) => id === deletedId);
    const isLastItem = deletedIndex === items.length - 1;

    return items[isLastItem ? deletedIndex - 1 : deletedIndex + 1];
};
