// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RefObject, useLayoutEffect, useState } from 'react';

import useResizeObserver from '@react-hook/resize-observer';

export function useSize<T extends HTMLElement>(target: RefObject<T>): DOMRect | undefined {
    const [size, setSize] = useState<DOMRect>();

    useLayoutEffect(() => {
        if (target.current !== null) {
            setSize(target.current.getBoundingClientRect());
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [target.current]);

    useResizeObserver(target, (entry) => {
        setSize(entry.target.getBoundingClientRect());
    });

    return size;
}
