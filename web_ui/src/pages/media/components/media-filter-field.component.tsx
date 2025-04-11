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

import { Item, Menu, MenuTrigger, Section, Text } from '@adobe/react-spectrum';

import { ChevronDownSmall } from '../../../assets/icons';
import { FilterItems, SearchRuleField } from '../../../core/media/media-filter.interface';
import { ActionButton } from '../../../shared/components/button/button.component';
import { getKeyConfig } from '../utils';

import classes from '../media-filter.module.scss';

interface MediaFilterFieldProps {
    value: SearchRuleField | '';
    onSelectionChange: (key: SearchRuleField) => void;
    fieldsOptions: FilterItems[][];
}

export const MediaFilterField = ({ onSelectionChange, value, fieldsOptions }: MediaFilterFieldProps): JSX.Element => {
    const keyConfig = getKeyConfig(fieldsOptions.flat(), value);

    return (
        <MenuTrigger>
            <ActionButton
                isQuiet
                id='media-filter-field'
                aria-label='media-filter-field'
                UNSAFE_className={[classes.mediaPicker, keyConfig.isPlaceHolder && classes.placeHolder].join(' ')}
            >
                <Text>{keyConfig.text}</Text>
                <ChevronDownSmall width={22} height={22} />
            </ActionButton>
            <Menu
                selectionMode='single'
                selectedKeys={[value?.toString() ?? '']}
                onAction={(key) => onSelectionChange(key as SearchRuleField)}
            >
                {fieldsOptions.map((section, index) => (
                    <Section key={index}>
                        {section.map(({ text, key }) => (
                            <Item textValue={text} key={key} aria-label={key.toLocaleLowerCase()}>
                                <Text>{text}</Text>
                            </Item>
                        ))}
                    </Section>
                ))}
            </Menu>
        </MenuTrigger>
    );
};
