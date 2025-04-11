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
