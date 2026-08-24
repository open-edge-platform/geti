// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, ReactNode, SetStateAction } from 'react';

import type { ConfigurableParameter, TrainingConfiguration } from '@/api/types';
import { Grid, minmax, Text, View } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { Accordion } from '../../components/accordion/accordion.component';
import { Parameters } from '../../components/parameters.component';
import { deepReplaceParameters } from '../../utils';
import { TilingModes } from './tiling-modes.component';
import {
    getAdaptiveTilingParameter,
    getCustomTilingParameters,
    getEnableTilingParameter,
    getTilingMode,
    TILING_MODES,
    TilingConfigurableParameterGroup,
    TilingMode,
} from './utils';

import classes from './tiling.module.scss';

type TilingProps = {
    tilingParameters: TilingConfigurableParameterGroup;
    onTrainingConfigurationChange: Dispatch<SetStateAction<TrainingConfiguration | undefined>>;
};

const changeTilingParameters = (
    trainingConfiguration: TrainingConfiguration,
    newConfigurationParameters: ConfigurableParameter[]
): TrainingConfiguration => {
    const parameters: TrainingConfiguration['parameters'] = deepReplaceParameters(
        trainingConfiguration.parameters,
        newConfigurationParameters,
        ['dataset_preparation', 'augmentation', 'tiling']
    );

    return { parameters };
};

export const Tiling = ({ tilingParameters, onTrainingConfigurationChange }: TilingProps) => {
    const { t } = useTranslation();
    const selectedTilingMode = getTilingMode(tilingParameters.parameters);
    const customTilingParameters = getCustomTilingParameters(tilingParameters.parameters);

    const handleTilingParametersChange = (newParameters: ConfigurableParameter[]) => {
        onTrainingConfigurationChange((config) => {
            if (config === undefined) return;

            return changeTilingParameters(config, newParameters);
        });
    };

    const handleTilingModeChange = (newTilingMode: TilingMode) => {
        const adaptiveParameter = getAdaptiveTilingParameter(tilingParameters.parameters);
        const enableParameter = getEnableTilingParameter(tilingParameters.parameters);

        if (adaptiveParameter === undefined || enableParameter === undefined) return;

        if (newTilingMode === TILING_MODES.AUTOMATIC) {
            handleTilingParametersChange([
                { ...enableParameter, value: true },
                { ...adaptiveParameter, value: true },
            ]);
        } else if (newTilingMode === TILING_MODES.OFF) {
            handleTilingParametersChange([
                { ...enableParameter, value: false },
                { ...adaptiveParameter, value: false },
            ]);
        } else if (newTilingMode === TILING_MODES.CUSTOM) {
            handleTilingParametersChange([
                { ...enableParameter, value: true },
                { ...adaptiveParameter, value: false },
            ]);
        }
    };

    const TILING_MODE_COMPONENTS: Record<TilingMode, ReactNode> = {
        [TILING_MODES.OFF]: (
            <Text UNSAFE_className={classes.tilingModeDescription} gridColumn={'2/3'}>
                {t('models.tilingOffDescription')}
            </Text>
        ),

        [TILING_MODES.AUTOMATIC]: (
            <Text UNSAFE_className={classes.tilingModeDescription} gridColumn={'2/3'}>
                {t('models.tilingAutoDescription')}
            </Text>
        ),
        [TILING_MODES.CUSTOM]: (
            <View gridColumn={'1/-1'}>
                <Parameters
                    parameters={customTilingParameters}
                    onChange={(parameter) => handleTilingParametersChange([parameter])}
                />
            </View>
        ),
    };

    return (
        <Accordion>
            <Accordion.Title>
                {t('models.tilingTitle')} <Accordion.Tag ariaLabel={t('models.tilingTagAria')}>{selectedTilingMode}</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>{t('models.tilingDescription')}</Accordion.Description>
                <Accordion.Divider marginY={'size-250'} />
                <Grid
                    columns={['size-3000', minmax('size-3400', '1fr'), 'size-400']}
                    gap={'size-300'}
                    alignItems={'center'}
                >
                    <TilingModes
                        description={tilingParameters.description}
                        selectedTilingMode={selectedTilingMode}
                        onTilingModeChange={handleTilingModeChange}
                    />
                    {TILING_MODE_COMPONENTS[selectedTilingMode]}
                </Grid>
            </Accordion.Content>
        </Accordion>
    );
};
