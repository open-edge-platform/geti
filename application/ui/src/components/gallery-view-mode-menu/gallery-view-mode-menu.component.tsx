// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { ActionButton, Item, Menu, MenuTrigger, ViewModes, type MediaViewModesProps } from '@geti-ui/ui';
import { Grid, GridMedium, GridSmall } from '@geti-ui/ui/icons';

type GalleryViewModeMenuProps = Pick<MediaViewModesProps, 'viewMode' | 'setViewMode'>;

export const GalleryViewModeMenu = ({ viewMode, setViewMode }: GalleryViewModeMenuProps) => {
    const { t } = useTranslation();
    const options = [
        { mode: ViewModes.LARGE, label: t('common.viewModes.large'), icon: Grid },
        { mode: ViewModes.MEDIUM, label: t('common.viewModes.medium'), icon: GridMedium },
        { mode: ViewModes.SMALL, label: t('common.viewModes.small'), icon: GridSmall },
    ];
    const Icon = options.find(({ mode }) => mode === viewMode)?.icon ?? Grid;

    return (
        <MenuTrigger>
            <ActionButton isQuiet aria-label={'View mode'}>
                <Icon fill={'#fff'} />
            </ActionButton>
            <Menu
                selectionMode={'single'}
                selectedKeys={[viewMode]}
                onAction={(key) => {
                    const selected = options.find(({ mode }) => mode === key);
                    if (selected && selected.mode !== viewMode) {
                        setViewMode(selected.mode);
                    }
                }}
            >
                {options.map(({ mode, label }) => (
                    <Item key={mode} textValue={label}>
                        {label}
                    </Item>
                ))}
            </Menu>
        </MenuTrigger>
    );
};
