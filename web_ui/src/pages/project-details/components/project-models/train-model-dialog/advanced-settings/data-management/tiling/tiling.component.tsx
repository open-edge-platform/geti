// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Content, ContextualHelp, Flex, Text, View } from '@adobe/react-spectrum';
import clsx from 'clsx';

import { Button } from '../../../../../../../../shared/components/button/button.component';
import { Accordion } from '../../accordion/accordion.component';

import styles from './tiling.module.scss';

enum TILING_MODES {
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

const TILING_MODE_DESCRIPTIONS: Record<TILING_MODES, string> = {
    [TILING_MODES.OFF]:
        'Model processes the entire image as a single unit without dividing it into smaller tiles. This approach is ' +
        'straightforward but may struggle with detecting small objects in high-resolution images, as the model might ' +
        'miss finer details',
    [TILING_MODES.Adaptive]:
        'Adaptive means that the system will automatically set the parameters ' +
        'based on the images resolution and annotations size.',
    [TILING_MODES.Manual]:
        'Manual allows users to specify the size, position of tiles and max number of object per tile ' +
        'manually. This approach provides greater control over the tiling process, enabling users to focus on ' +
        'specific areas of interest within the image.',
};

const TilingModes: FC<TilingModesProps> = ({ selectedTilingMode, onTilingModeChange }) => {
    return (
        <View>
            <Flex marginBottom={'size-200'}>
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
            <Text UNSAFE_className={styles.tilingModeDescription}>{TILING_MODE_DESCRIPTIONS[selectedTilingMode]}</Text>
        </View>
    );
};

export const Tiling: FC = () => {
    const [selectedTilingMode, setSelectedTilingMode] = useState<TILING_MODES>(TILING_MODES.Adaptive);

    return (
        <Accordion>
            <Accordion.Title>
                Tiling<Accordion.Tag>{selectedTilingMode}</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Flex gap={'size-1000'}>
                    <Text UNSAFE_className={styles.title}>
                        Tiling mode <TilingModeTooltip />
                    </Text>
                    <TilingModes selectedTilingMode={selectedTilingMode} onTilingModeChange={setSelectedTilingMode} />
                </Flex>
            </Accordion.Content>
        </Accordion>
    );
};
