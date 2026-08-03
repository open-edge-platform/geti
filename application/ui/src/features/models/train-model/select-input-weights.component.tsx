// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Content, ContextualHelp, Heading, Item, Picker } from '@geti-ui/ui';

import { useTrainModelState } from './train-model-provider.component';

export const SelectInputWeights = () => {
    const { inputWeights, selectedInputWeightsId, onSelectInputWeightsId } = useTrainModelState();

    return (
        <Picker
            flex={1}
            items={inputWeights}
            label={'Select input weights'}
            selectedKey={selectedInputWeightsId}
            onSelectionChange={(key) => onSelectInputWeightsId(String(key))}
            contextualHelp={
                <ContextualHelp variant={'info'} placement={'top'}>
                    <Heading>Selecting input weights</Heading>
                    <Content>
                        {'Choose an existing model revision to continue fine-tuning, or select ' +
                            `"Default pre-trained weights" to fine-tune a new model starting from ` +
                            'publicly available weights pre-trained on large public datasets.'}
                    </Content>
                </ContextualHelp>
            }
        >
            {(item) => <Item key={item.id}>{item.name}</Item>}
        </Picker>
    );
};
