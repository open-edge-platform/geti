// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Item, Loading, Picker, Text, View } from '@geti/ui';

import { hasEqualId } from '../../../../shared/utils';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { SelectableOptimizationType } from '../../project-details.interface';

interface SelectOptimizationProps {
    options: SelectableOptimizationType[];
    selectedOptimizationType: SelectableOptimizationType;
    setSelectedOptimizationType: (optimizationType: SelectableOptimizationType) => void;
    isLoading: boolean;
}

export const SelectOptimization = ({
    options,
    selectedOptimizationType,
    setSelectedOptimizationType,
    isLoading,
}: SelectOptimizationProps): JSX.Element => {
    const handleSelectOptimizationModel = (key: Key) => {
        const selectedOption = options.find(hasEqualId(key.toString()));

        if (selectedOption) {
            setSelectedOptimizationType(selectedOption);
        }
    };

    return (
        <View>
            {isLoading ? (
                <View marginY={'size-225'}>
                    <Loading mode='inline' size={'M'} />
                </View>
            ) : (
                <Picker
                    label={'Optimization'}
                    placeholder={'Select optimization model'}
                    id={'select-optimized-model-group-id'}
                    items={options}
                    width={'100%'}
                    selectedKey={selectedOptimizationType.id}
                    onSelectionChange={handleSelectOptimizationModel}
                >
                    {(item) => (
                        <Item key={item.id} textValue={item.text}>
                            <Text id={`${item.id}-${idMatchingFormat(item.text)}-id`}>{item.text}</Text>
                        </Item>
                    )}
                </Picker>
            )}
        </View>
    );
};
