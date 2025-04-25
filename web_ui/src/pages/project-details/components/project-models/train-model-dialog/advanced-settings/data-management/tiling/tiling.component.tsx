// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode, useState } from 'react';

import { Grid, minmax, Text, View } from '@adobe/react-spectrum';

import {
    ConfigurableParametersComponents,
    NumberGroupParams,
} from '../../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { Accordion } from '../../accordion/accordion.component';
import { TILING_MODES, TilingModes } from './tiling-modes.component';
import { TilingOptions } from './tiling-options.component';

import styles from './tiling.module.scss';

interface TilingProps {
    tilingParameters: ConfigurableParametersComponents;
}

const getTilingMode = (tilingParameters: ConfigurableParametersComponents): TILING_MODES => {
    const adaptive = tilingParameters?.parameters?.find((parameter) => parameter.name === 'enable_adaptive_params');
    const enablingTiling = tilingParameters?.parameters?.find((parameter) => parameter.name === 'enable_tiling');

    if (adaptive !== undefined && adaptive.value === true) {
        return TILING_MODES.Adaptive;
    }

    if (enablingTiling !== undefined && enablingTiling.value === false) {
        return TILING_MODES.OFF;
    }

    return TILING_MODES.Manual;
};

export const Tiling: FC<TilingProps> = ({ tilingParameters }) => {
    const [selectedTilingMode, setSelectedTilingMode] = useState<TILING_MODES>(() => getTilingMode(tilingParameters));

    const manualTilingParameters = (tilingParameters.parameters?.filter(
        (parameter) =>
            !['enable_adaptive_params', 'enable_tiling'].includes(parameter.name) &&
            ['integer', 'float'].includes(parameter.dataType)
    ) ?? []) as NumberGroupParams[];

    console.log({ tilingParameters, manualTilingParameters });

    const TILING_MODE_COMPONENTS: Record<TILING_MODES, ReactNode> = {
        [TILING_MODES.OFF]: (
            <Text UNSAFE_className={styles.tilingModeDescription} gridColumn={'2/3'}>
                Model processes the entire image as a single unit without dividing it into smaller tiles. This approach
                is straightforward but may struggle with detecting small objects in high-resolution images, as the model
                might miss finer details
            </Text>
        ),

        [TILING_MODES.Adaptive]: (
            <View UNSAFE_className={styles.tilingModeDescription} gridColumn={'2/3'}>
                Adaptive means that the system will automatically set the parameters based on the images resolution and
                annotations size.
            </View>
        ),
        [TILING_MODES.Manual]: <TilingOptions parameters={manualTilingParameters} />,
    };

    return (
        <Accordion>
            <Accordion.Title>
                Tiling<Accordion.Tag>{selectedTilingMode}</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>
                    Tiling is a technique that divides high-resolution images into smaller tiles and might be useful to
                    increase accuracy for small object detection tasks.
                </Accordion.Description>
                <Accordion.Divider marginY={'size-200'} />
                <Grid
                    columns={['max-content', minmax('size-3400', '1fr'), 'size-400']}
                    gap={'size-300'}
                    alignItems={'center'}
                >
                    <TilingModes selectedTilingMode={selectedTilingMode} onTilingModeChange={setSelectedTilingMode} />
                    {TILING_MODE_COMPONENTS[selectedTilingMode]}
                </Grid>
            </Accordion.Content>
        </Accordion>
    );
};
