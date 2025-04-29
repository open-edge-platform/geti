// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, Key, SetStateAction } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import capitalize from 'lodash/capitalize';

import { Grid, GridMedium, GridSmall, List } from '../../../assets/icons';
import { MenuTriggerButton } from '../menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { VIEW_MODE_LABEL, ViewModes } from './utils';

interface MediaViewModesProps {
    items?: ViewModes[];
    viewMode: ViewModes;
    isDisabled?: boolean;
    setViewMode: Dispatch<SetStateAction<ViewModes>>;
}

const ICON_PER_MODE: Record<ViewModes, JSX.Element> = {
    [ViewModes.DETAILS]: <List />,
    [ViewModes.SMALL]: <GridSmall />,
    [ViewModes.MEDIUM]: <GridMedium />,
    [ViewModes.LARGE]: <Grid />,
};

const ITEMS = [ViewModes.LARGE, ViewModes.MEDIUM, ViewModes.SMALL, ViewModes.DETAILS];

const MediaViewMode = (item: string): JSX.Element => {
    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            {ICON_PER_MODE[item as ViewModes]}
            <Text>{item}</Text>
        </Flex>
    );
};

export const MediaViewModes = ({
    viewMode,
    items = ITEMS,
    isDisabled = false,
    setViewMode,
}: MediaViewModesProps): JSX.Element => {
    const handleAction = (key: Key): void => {
        const convertedKeyToViewMode = capitalize(String(key));

        if (convertedKeyToViewMode === viewMode) {
            return;
        }

        setViewMode(convertedKeyToViewMode as ViewModes);
    };

    return (
        <MenuTriggerButton
            id={'view-mode-id'}
            ariaLabel={VIEW_MODE_LABEL}
            title={VIEW_MODE_LABEL}
            items={items}
            onAction={handleAction}
            icon={ICON_PER_MODE[viewMode]}
            renderContent={MediaViewMode}
            isDisabled={isDisabled}
            selectedKey={[viewMode.toLocaleLowerCase()]}
            tooltipPlacement={'bottom'}
        />
    );
};
