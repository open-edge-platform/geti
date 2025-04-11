// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import { CTRL_OR_COMMAND_KEY } from '../../../shared/hotkeys';
import { DefaultHotkeys, Hotkeys } from '../providers/annotator-provider/utils';
import { GrabcutHotKeys } from '../tools/grabcut-tool/grabcut-tool.interface';
import { PolygonHotKeys } from '../tools/polygon-tool/polygon-tool.interface';
import { SelectingHotKeys } from '../tools/selecting-tool/selecting.interface';

export const useAnnotatorHotkeys = (): { hotkeys: Hotkeys } => {
    const hotkeys = useMemo(
        () => ({
            ...DefaultHotkeys(CTRL_OR_COMMAND_KEY),
            ...GrabcutHotKeys,
            ...PolygonHotKeys,
            ...SelectingHotKeys,
        }),
        []
    );

    return { hotkeys };
};
