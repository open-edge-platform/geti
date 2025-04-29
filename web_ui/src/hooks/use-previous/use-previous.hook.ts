// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

export function usePrevious<T>(value: T): T | undefined {
    const previous = useRef<T>();

    useEffect(() => {
        previous.current = value;
    }, [value]);

    return previous.current;
}
