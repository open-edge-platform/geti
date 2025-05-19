// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Item, Menu, MenuTrigger as MenuTriggerSpectrum, Text, TooltipTrigger } from '@geti/ui';
import { isEmpty, isFunction } from 'lodash-es';

import { idMatchingFormat } from '../../../test-utils/id-utils';
import { MenuTriggerProps } from '../upload-media/upload-media-button/upload-media-button.interface';

import classes from './menu-trigger.module.scss';

export const MenuTrigger = ({
    id,
    items,
    menuTooltip,
    selectedKey,
    disabledKeys,
    onAction,
    onOpenChange,
    renderContent,
    children,
    ariaLabel,
}: MenuTriggerProps): JSX.Element => {
    return (
        <MenuTriggerSpectrum onOpenChange={onOpenChange}>
            {children}

            <TooltipTrigger isDisabled={isEmpty(disabledKeys)}>
                <Menu
                    id={`${id}-menu-id`}
                    aria-label={`${ariaLabel}-Menu`}
                    onAction={onAction}
                    disabledKeys={disabledKeys?.map((key) => String(key).toLocaleLowerCase())}
                    selectedKeys={selectedKey}
                    selectionMode={selectedKey ? 'single' : undefined}
                    UNSAFE_style={{ pointerEvents: 'auto' }}
                    UNSAFE_className={selectedKey ? classes.menuList : undefined}
                >
                    {items.map((item: string) => (
                        <Item key={item.toLocaleLowerCase()} aria-label={item.toLocaleLowerCase()} textValue={item}>
                            <Text
                                id={`${idMatchingFormat(item.toLowerCase())}-id`}
                                UNSAFE_style={{ pointerEvents: 'all' }}
                            >
                                {isFunction(renderContent) ? renderContent(item) : item}
                            </Text>
                        </Item>
                    ))}
                </Menu>

                <Text>{menuTooltip}</Text>
            </TooltipTrigger>
        </MenuTriggerSpectrum>
    );
};
