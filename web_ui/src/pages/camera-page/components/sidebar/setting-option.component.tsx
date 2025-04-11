// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key, useState } from 'react';

import { Flex, Heading, Item, Picker, Slider, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import capitalize from 'lodash/capitalize';
import words from 'lodash/words';

import { Revisit } from '../../../../assets/icons';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { DeviceConfiguration } from '../../providers/util';

import classes from './sidebar.module.scss';

export interface SettingOptionProps {
    label: string;
    config: DeviceConfiguration['config'];
    onChange: (num: number | string) => void;
}

const unFormatText = (text: string) => words(text).join(' ');

export const SettingOption = ({ label, config, onChange }: SettingOptionProps) => {
    const [value, setValue] = useState<number | string>(config.value);

    const updateValue = (key: Key) => {
        setValue(String(key));
        onChange(String(key));
    };

    return (
        <>
            <Flex
                marginTop={'size-200'}
                marginBottom={'size-50'}
                justifyContent={'space-between'}
                alignItems={'center'}
            >
                <Heading level={4} margin={0}>
                    {capitalize(unFormatText(label))}
                </Heading>

                <TooltipTrigger placement={'bottom'}>
                    <QuietActionButton aria-label={`reset ${label}`} onPress={() => updateValue(config.value)}>
                        <Revisit />
                    </QuietActionButton>
                    <Tooltip>{`Reset ${label}`}</Tooltip>
                </TooltipTrigger>
            </Flex>

            {config.type === 'selection' ? (
                <Picker
                    width={'100%'}
                    aria-label={`${label} selection options`}
                    items={config.options.map((name) => ({ id: name, name }))}
                    onSelectionChange={updateValue}
                    selectedKey={value}
                >
                    {(item) => <Item key={item.id}>{item.name}</Item>}
                </Picker>
            ) : (
                <Slider
                    label=' '
                    width={'100%'}
                    value={Number(value)}
                    minValue={config.min}
                    maxValue={config.max}
                    labelPosition='side'
                    onChange={updateValue}
                    aria-label={`${label} slider options`}
                    UNSAFE_className={classes.cameraSettingSlider}
                />
            )}
        </>
    );
};
