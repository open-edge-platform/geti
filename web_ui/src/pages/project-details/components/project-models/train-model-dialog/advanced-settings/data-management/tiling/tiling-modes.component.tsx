// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Content, ContextualHelp, Flex, Text } from '@adobe/react-spectrum';
import clsx from 'clsx';

import { Button } from '../../../../../../../../shared/components/button/button.component';

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

interface TilingModeButtonProps {
    tilingMode: TILING_MODES;
    selectedTilingMode: TILING_MODES;
    onTilingModeChange: (mode: TILING_MODES) => void;
    className: string | undefined;
}

const TilingModeButton: FC<TilingModeButtonProps> = ({
    tilingMode,
    selectedTilingMode,
    onTilingModeChange,
    className,
}) => {
    return (
        <Button
            variant={selectedTilingMode === tilingMode ? 'accent' : 'secondary'}
            UNSAFE_className={clsx(styles.optionButton, className)}
            onPress={() => {
                onTilingModeChange(tilingMode);
            }}
        >
            {tilingMode}
        </Button>
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
                <TilingModeButton
                    tilingMode={TILING_MODES.OFF}
                    selectedTilingMode={selectedTilingMode}
                    onTilingModeChange={onTilingModeChange}
                    className={selectedTilingMode === TILING_MODES.Adaptive ? styles.offMode : undefined}
                />
                <TilingModeButton
                    tilingMode={TILING_MODES.Adaptive}
                    selectedTilingMode={selectedTilingMode}
                    onTilingModeChange={onTilingModeChange}
                    className={selectedTilingMode !== TILING_MODES.Adaptive ? styles.adaptiveMode : undefined}
                />
                <TilingModeButton
                    tilingMode={TILING_MODES.Manual}
                    selectedTilingMode={selectedTilingMode}
                    onTilingModeChange={onTilingModeChange}
                    className={selectedTilingMode === TILING_MODES.Adaptive ? styles.manualMode : undefined}
                />
            </Flex>
        </>
    );
};
