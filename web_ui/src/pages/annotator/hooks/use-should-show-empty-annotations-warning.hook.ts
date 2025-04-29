// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import isEmpty from 'lodash/isEmpty';

import { useSelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTaskChain } from '../providers/task-chain-provider/task-chain-provider.component';
import { useTask } from '../providers/task-provider/task-provider.component';

export const useShouldShowEmptyAnnotationsWarning = (): boolean => {
    const { selectedMediaItem } = useSelectedMediaItem();
    const { isTaskChainSecondTask } = useTask();
    const { inputs: inputAnnotations } = useTaskChain();

    return useMemo(() => {
        if (selectedMediaItem === undefined) {
            return false;
        }

        return isEmpty(inputAnnotations) && isTaskChainSecondTask;
    }, [inputAnnotations, selectedMediaItem, isTaskChainSecondTask]);
};
