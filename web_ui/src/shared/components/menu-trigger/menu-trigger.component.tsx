// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Item, Menu, MenuTrigger as MenuTriggerSpectrum, Text, TooltipTrigger } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isFunction from 'lodash/isFunction';

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
