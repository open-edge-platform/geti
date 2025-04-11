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

import { Key } from 'react';

import { Item, Picker, Text, View } from '@adobe/react-spectrum';

import { LoadingIndicator } from '../../../../shared/components/loading/loading-indicator.component';
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
                    <LoadingIndicator size={'M'} />
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
