// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue } from '@geti/ui';

import { LinkButton } from '../../link-button/link-button.component';
import { MenuTriggerProps } from '../../upload-media/upload-media-button/upload-media-button.interface';
import { MenuTrigger } from '../menu-trigger.component';

interface MenuTriggerLinkProps extends MenuTriggerProps {
    text: string;
    isDisabled?: boolean;
}

export const MenuTriggerLink = ({
    items,
    onAction,
    disabledKeys,
    menuTooltip,
    onOpenChange,
    id,
    ariaLabel,
    text,
    isDisabled,
}: Omit<MenuTriggerLinkProps, 'children'>): JSX.Element => {
    return (
        <MenuTrigger
            id={id}
            items={items}
            onAction={onAction}
            menuTooltip={menuTooltip}
            disabledKeys={disabledKeys}
            onOpenChange={onOpenChange}
            ariaLabel={ariaLabel}
        >
            <LinkButton text={text} isDisabled={isDisabled} UNSAFE_style={{ fontSize: dimensionValue('size-225') }} />
        </MenuTrigger>
    );
};
