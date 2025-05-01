// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { ConfigurableParameters } from '@shared/components/configurable-parameters/configurable-parameters.component';
import { ConfigurableParametersType } from '@shared/components/configurable-parameters/configurable-parameters.interface';
import { Loading } from '@shared/components/loading/loading.component';

import { useConfigParameters } from '../../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import { useModelIdentifier } from '../../../../../hooks/use-model-identifier/use-model-identifier.hook';

interface ModelConfigurableParametersProps {
    taskId: string;
}

export const ModelConfigurableParameters = ({ taskId }: ModelConfigurableParametersProps): JSX.Element => {
    const { modelId, ...projectIdentifier } = useModelIdentifier();
    const { useGetModelConfigParameters } = useConfigParameters(projectIdentifier);
    const { isLoading, data } = useGetModelConfigParameters({ taskId, modelId });

    return isLoading ? (
        <Loading />
    ) : data ? (
        <View marginTop={'size-250'} height={'100%'}>
            <ConfigurableParameters
                type={ConfigurableParametersType.READ_ONLY_SINGLE_PARAMETERS}
                configParametersData={data}
            />
        </View>
    ) : (
        <></>
    );
};
