// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Text, ToggleButtons } from '@geti/ui';

import { Tooltip } from '../../ui/tooltip.component';

import styles from './tiling.module.scss';

export enum TILING_MODES {
    OFF = 'Off',
    Adaptive = 'Adaptive',
    Manual = 'Manual',
}

const TilingModeTooltip: FC = () => {
    return (
        <Tooltip>
            Tiling is a technique that divides high-resolution images into smaller tiles and might be useful to increase
            accuracy for small object detection tasks.
        </Tooltip>
    );
};

interface TilingModesProps {
    selectedTilingMode: TILING_MODES;
    onTilingModeChange: (tilingMode: TILING_MODES) => void;
}

export const TilingModes: FC<TilingModesProps> = ({ selectedTilingMode, onTilingModeChange }) => {
    return (
        <>
            <Text UNSAFE_className={styles.title} width={'size-3000'}>
                Tiling mode <TilingModeTooltip />
            </Text>
            <ToggleButtons
                options={[TILING_MODES.OFF, TILING_MODES.Adaptive, TILING_MODES.Manual]}
                selectedOption={selectedTilingMode}
                onOptionChange={onTilingModeChange}
            />
        </>
    );
};
