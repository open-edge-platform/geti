// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, RefObject, useEffect, useState } from 'react';

import { useIntersectionObserver } from 'usehooks-ts';

type LazyLoadSectionProps = {
    children: ReactNode;
    rootRef: RefObject<HTMLDivElement | null>;
};

export const LazyLoadSection = ({ children, rootRef }: LazyLoadSectionProps) => {
    // The scroll container is an ancestor, so its ref is still null on our first render
    const [root, setRoot] = useState<HTMLDivElement | null>(null);

    useEffect(() => {
        setRoot(rootRef.current);
    }, [rootRef]);

    const { ref, isIntersecting } = useIntersectionObserver({
        threshold: 0,
        root,
        rootMargin: '150px',
        freezeOnceVisible: true,
    });

    return (
        // It's safe to assume that min height is at least 50px. This value is used by the intersection observer to
        // trigger element rendering.
        <div ref={ref} style={{ minHeight: '50px' }}>
            {isIntersecting && children}
        </div>
    );
};
