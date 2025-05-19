// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DependencyList, useEffect } from 'react';

import { isNil } from 'lodash-es';

interface useGetTargetPositionProps {
    gap: number;
    delay?: number;
    container?: Element | null;
    targetIndex?: number;
    dependencies?: DependencyList;
    callback: (scrollTo: number) => void;
}

const isValidIndex = (index?: number): index is number => !isNil(index) && Number.isInteger(index) && index >= 0;

export const useGetTargetPosition = ({
    gap,
    delay = 500,
    container,
    targetIndex,
    dependencies = [],
    callback,
}: useGetTargetPositionProps) => {
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            if (!container || !isValidIndex(targetIndex)) {
                return;
            }

            const containerWidth = container.clientWidth;
            const childrenWidth = container.firstElementChild?.clientWidth ?? 1;
            const childrenHeight = container.firstElementChild?.clientHeight ?? 1;
            const childrenPerRow = Math.floor(containerWidth / childrenWidth);
            const targetRow = Math.floor(targetIndex / childrenPerRow);
            const scrollTo = (childrenHeight + gap) * targetRow;

            callback(scrollTo);
            // we don't want to scroll immediately
            // in case of changed view mode we have to scroll once view is rendered
        }, delay);

        return () => {
            timeoutId && clearTimeout(timeoutId);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, dependencies);
};
