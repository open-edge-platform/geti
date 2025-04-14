// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
