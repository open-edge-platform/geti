// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { DOMAIN } from '../../../core/projects/core.interface';
import { useAvailabilityOfHotkeys } from '../../annotator/components/primary-toolbar/hot-keys-button/use-availability-of-hotkeys.hook';
import { useAnnotatorHotkeys } from '../../annotator/hooks/use-hotkeys-configuration.hook';
import { HotKeyActions } from '../../annotator/providers/annotator-provider/utils';

export const useUsedAnnotatorHotkeys = (domains: DOMAIN[]): string[] => {
    const { hotkeys } = useAnnotatorHotkeys();
    const availabilityOfHotkeys = useAvailabilityOfHotkeys(domains);

    return useMemo(
        () =>
            Object.entries(hotkeys)
                .filter(([hotkeyName]) => {
                    return availabilityOfHotkeys[hotkeyName as HotKeyActions];
                })
                .map(([_, hotkeyValue]) => hotkeyValue.toLocaleLowerCase()),
        [availabilityOfHotkeys, hotkeys]
    );
};
