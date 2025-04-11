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

import { Key } from 'react';

import { Item, Picker, Section } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import { LabelTag } from '../../components/labels/label-tag/label-tag.component';
import { WatershedLabel } from './watershed-tool.interface';

import classes from './secondary-toolbar.module.scss';

interface LabelPickerProps {
    availableLabels: WatershedLabel[];
    backgroundLabel: WatershedLabel;
    handleSelectLabel: (key: Key) => void;
}

export const LabelPicker = ({ availableLabels, backgroundLabel, handleSelectLabel }: LabelPickerProps): JSX.Element => {
    return (
        <Picker
            label='Select label'
            labelPosition='side'
            aria-label={'label'}
            id='picker-label'
            placeholder={'Select label'}
            width='size-2400'
            items={availableLabels}
            defaultSelectedKey={availableLabels[0].label.name}
            onSelectionChange={handleSelectLabel}
            UNSAFE_className={classes.picker}
        >
            <Section>
                <Item key={backgroundLabel.label.name} textValue={backgroundLabel.label.name}>
                    <Text id={`option-${backgroundLabel.label.name}`}>
                        <LabelTag id={`option-${backgroundLabel.label.name}`} label={backgroundLabel.label} />
                    </Text>
                </Item>
            </Section>
            <Section>
                {availableLabels.map((labelItem: WatershedLabel) => (
                    <Item key={labelItem.label.name} textValue={labelItem.label.name}>
                        <Text id={`option-${labelItem.label.name}`}>
                            <LabelTag id={`option-${labelItem.label.name}`} label={labelItem.label} />
                        </Text>
                    </Item>
                ))}
            </Section>
        </Picker>
    );
};
