// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';

import { idMatchingFormat } from '../../../test-utils/id-utils';
import { TabItem } from '../tabs/tabs.interface';
import { ConfigurableParametersProps, ConfigurableParametersType } from './configurable-parameters.interface';
import { CPGroupsList } from './cp-groups-list/cp-groups-list.component';
import { CPParamsList } from './cp-list/cp-list.component';
import { SelectableCustomizedTabs } from './selectable-customized-tabs/selectable-customized-tabs.component';
import { SelectableManyTasks } from './selectable-many-tasks/selectable-many-tasks.component';
import { isLearningParametersTab } from './utils';

export const ConfigurableParameters = (props: ConfigurableParametersProps): JSX.Element => {
    if (props.type === ConfigurableParametersType.MANY_CONFIG_PARAMETERS) {
        const {
            configParametersData,
            updateParameter,
            selectedComponent,
            selectedComponentId,
            setSelectedComponentId,
        } = props;

        return (
            <View minHeight={0} height='100%'>
                <SelectableManyTasks
                    configurableParameters={configParametersData}
                    updateParameter={updateParameter}
                    selectedComponent={selectedComponent}
                    selectedComponentId={selectedComponentId}
                    setSelectedComponentId={setSelectedComponentId}
                />
            </View>
        );
    } else {
        let ITEMS: TabItem[] = [];

        if (props.type === ConfigurableParametersType.SINGLE_CONFIG_PARAMETERS) {
            const { updateParameter, configParametersData } = props;

            ITEMS = configParametersData.components.map(({ header, groups, parameters, entityIdentifier }) => {
                const isLearningParameters = isLearningParametersTab(entityIdentifier);

                return {
                    id: `${idMatchingFormat(header)}-id`,
                    key: `${idMatchingFormat(header)}-id`,
                    name: header,
                    isLearningParametersTab: isLearningParameters,
                    children: (
                        <View marginX={{ base: '0', L: 'size-250' }}>
                            {parameters && (
                                <CPParamsList
                                    parameters={parameters}
                                    updateParameter={updateParameter}
                                    header={header}
                                />
                            )}
                            {groups && <CPGroupsList groups={groups} updateParameter={updateParameter} />}
                        </View>
                    ),
                };
            });
        } else {
            ITEMS = props.configParametersData.components.map(({ header, groups, parameters }) => ({
                id: `${idMatchingFormat(header)}-id`,
                key: `${idMatchingFormat(header)}-id`,
                name: header,
                children: (
                    <>
                        {parameters && <CPParamsList parameters={parameters} header={header} />}
                        {groups && <CPGroupsList groups={groups} />}
                    </>
                ),
            }));
        }

        return (
            <View minHeight={0} height={'100%'}>
                <SelectableCustomizedTabs items={ITEMS} orientation={'vertical'} height={'100%'} />
            </View>
        );
    }
};
