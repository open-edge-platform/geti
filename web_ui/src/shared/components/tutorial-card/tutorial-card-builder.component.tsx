// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
