// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Item, Picker, Section, Text } from '@geti/ui';

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
            aria-label={'watershed label picker'}
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
