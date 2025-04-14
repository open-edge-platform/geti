// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
