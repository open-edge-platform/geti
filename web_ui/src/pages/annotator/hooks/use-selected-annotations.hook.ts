// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useVisibleAnnotations } from './use-visible-annotations.hook';

export const useSelectedAnnotations = (isAnnotationLocked: boolean | undefined = undefined) => {
    const visibleAnnotations = useVisibleAnnotations();

    return useMemo(() => {
        if (isAnnotationLocked !== undefined) {
            return visibleAnnotations.filter(
                ({ isSelected, isLocked }) => isSelected && isLocked === isAnnotationLocked
            );
        }

        return visibleAnnotations.filter(({ isSelected }) => isSelected);
    }, [visibleAnnotations, isAnnotationLocked]);
};
