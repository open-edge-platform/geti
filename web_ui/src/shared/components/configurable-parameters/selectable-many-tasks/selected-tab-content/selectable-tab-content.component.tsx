// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@geti/ui';

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
