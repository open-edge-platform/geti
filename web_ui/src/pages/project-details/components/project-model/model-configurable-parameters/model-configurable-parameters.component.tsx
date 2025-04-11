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

import { useConfigParameters } from '../../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import { useModelIdentifier } from '../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { ConfigurableParameters } from '../../../../../shared/components/configurable-parameters/configurable-parameters.component';
import { ConfigurableParametersType } from '../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { Loading } from '../../../../../shared/components/loading/loading.component';

interface ModelConfigurableParametersProps {
    taskId: string;
}

export const ModelConfigurableParameters = ({ taskId }: ModelConfigurableParametersProps): JSX.Element => {
    const { modelId, ...projectIdentifier } = useModelIdentifier();
    const { useGetModelConfigParameters } = useConfigParameters(projectIdentifier);
    const { isLoading, data } = useGetModelConfigParameters(taskId, modelId);

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
