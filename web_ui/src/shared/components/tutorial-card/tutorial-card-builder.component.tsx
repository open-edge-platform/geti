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

import { CSSProperties } from 'react';

import { TUTORIAL_CARD_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { useTutorialEnablement } from '../../hooks/use-tutorial-enablement.hook';
import { TutorialCard } from './tutorial-card.component';

interface TutorialCardBuilderProps {
    cardKey: TUTORIAL_CARD_KEYS;
    styles?: CSSProperties;
}

const DEFAULT_BOTTOM_MARGIN = 'var(--spectrum-global-dimension-size-150)';

export const TutorialCardBuilder = ({ cardKey, styles }: TutorialCardBuilderProps): JSX.Element => {
    const settings = useUserGlobalSettings();

    const currentStyles = {
        marginBottom: DEFAULT_BOTTOM_MARGIN,
        ...styles,
    };

    const { close, isOpen, dismissAll } = useTutorialEnablement(cardKey);

    if (!isOpen) {
        return <></>;
    }

    return (
        <TutorialCard
            id={cardKey}
            styles={currentStyles}
            onPressDismiss={close}
            isLoading={settings.isSavingConfig}
            onPressDismissAll={dismissAll}
        />
    );
};
