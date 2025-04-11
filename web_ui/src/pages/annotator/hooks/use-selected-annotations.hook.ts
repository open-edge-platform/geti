// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
