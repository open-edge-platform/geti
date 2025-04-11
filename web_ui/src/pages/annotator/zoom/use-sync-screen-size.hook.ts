// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { RefObject, useEffect, useRef } from 'react';

import { useSize } from '../../../hooks/use-size/use-size.hook';
import { useZoom } from './zoom-provider.component';

export const useSyncScreenSize = (): RefObject<HTMLDivElement> => {
    const { setScreenSize } = useZoom();
    const ref = useRef<HTMLDivElement>(null);
    const screenSize = useSize(ref);

    // In Chrome on Windows useSize returns a float instead of integer, which
    // introduces subtle bugs where any useEffect relying on the screenSize
    // will be called whenever we rerender this hook
    const width = screenSize === undefined ? undefined : Math.round(screenSize.width);
    const height = screenSize === undefined ? undefined : Math.round(screenSize.height);

    useEffect(() => {
        if (height === undefined || width === undefined) {
            return;
        }

        setScreenSize((previousScreenSize) => {
            if (previousScreenSize?.width !== width || previousScreenSize?.height !== height) {
                return { width, height };
            }

            return previousScreenSize;
        });
    }, [width, height, setScreenSize]);

    return ref;
};
