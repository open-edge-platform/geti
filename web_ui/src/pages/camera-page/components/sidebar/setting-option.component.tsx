// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useState } from 'react';

import { Flex, Heading, Item, Picker, Slider, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';
import capitalize from 'lodash/capitalize';
import words from 'lodash/words';

import { Revisit } from '../../../../assets/icons';
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
