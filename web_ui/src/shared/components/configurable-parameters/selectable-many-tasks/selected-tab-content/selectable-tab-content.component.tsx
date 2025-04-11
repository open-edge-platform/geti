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

import { View } from '@adobe/react-spectrum';

import { ConfigurableParametersMany } from '../../configurable-parameters.interface';
import { CPDescription } from '../../cp-description/cp-description.component';
import { CPGroupsList } from '../../cp-groups-list/cp-groups-list.component';
import { CPParamsList } from '../../cp-list/cp-list.component';

type SelectableTabContentProps = Pick<ConfigurableParametersMany, 'selectedComponent' | 'updateParameter'>;

export const SelectableTabContent = ({
    selectedComponent,
    updateParameter,
}: SelectableTabContentProps): JSX.Element => {
    return (
        <View UNSAFE_style={{ overflowY: 'auto', overflowX: 'hidden' }} flex={1} marginX={'size-250'}>
            {selectedComponent?.description && (
                <CPDescription id={`${selectedComponent.id}-description`} description={selectedComponent.description} />
            )}
            {selectedComponent?.parameters && (
                <CPParamsList
                    parameters={selectedComponent.parameters}
                    updateParameter={updateParameter}
                    header={selectedComponent?.header}
                />
            )}
            {selectedComponent?.groups && (
                <CPGroupsList groups={selectedComponent.groups} updateParameter={updateParameter} />
            )}
        </View>
    );
};
