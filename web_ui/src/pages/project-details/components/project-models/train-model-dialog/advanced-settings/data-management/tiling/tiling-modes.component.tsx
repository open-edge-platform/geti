// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Content, ContextualHelp, Flex, Text } from '@adobe/react-spectrum';

import { OptionsButtons } from '../ui/options-buttons/options-buttons.component';

import styles from './tiling.module.scss';

export enum TILING_MODES {
    OFF = 'Off',
    Adaptive = 'Adaptive',
    Manual = 'Manual',
}

const TilingModeTooltip: FC = () => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>
                    Tiling is a technique that divides high-resolution images into smaller tiles and might be useful to
                    increase accuracy for small object detection tasks.
                </Text>
            </Content>
        </ContextualHelp>
    );
};

interface TilingModesProps {
    selectedTilingMode: TILING_MODES;
    onTilingModeChange: (tilingMode: TILING_MODES) => void;
}

export const TilingModes: FC<TilingModesProps> = ({ selectedTilingMode, onTilingModeChange }) => {
    return (
        <>
            <Text UNSAFE_className={styles.title} gridColumn={'1/2'}>
                Tiling mode <TilingModeTooltip />
            </Text>
            <Flex gridColumn={'2/3'}>
                <OptionsButtons
                    options={[TILING_MODES.OFF, TILING_MODES.Adaptive, TILING_MODES.Manual]}
                    selectedOption={selectedTilingMode}
                    onOptionChange={onTilingModeChange}
                />
            </Flex>
        </>
    );
};
