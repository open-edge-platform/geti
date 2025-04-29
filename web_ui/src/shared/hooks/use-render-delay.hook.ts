// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

export const useRenderDelay = (delay: number): boolean => {
    const [isShown, setIsShown] = useState(!delay);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsShown(true);
        }, delay);
        return () => clearTimeout(timer);
    }, [delay]);

    return isShown;
};
