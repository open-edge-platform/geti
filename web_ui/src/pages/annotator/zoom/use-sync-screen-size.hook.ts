// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
