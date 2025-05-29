// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text } from '@geti/ui';

import { ThreeDotsFlashing } from '../../../../../../shared/components/three-dots-flashing/three-dots-flashing.component';

import classes from './model-card.module.scss';

const ModelInfoTraining = () => (
    <>
        <Text UNSAFE_className={classes.modelInfo} data-testid={'model-size-id'}>
            Model weight size: <ThreeDotsFlashing className={classes.threeDotsFlashing} />
        </Text>
        <Text marginX={'size-50'}>|</Text>
        <Text UNSAFE_className={classes.modelInfo} data-testid={'total-disk-size-id'}>
            Total size: <ThreeDotsFlashing className={classes.threeDotsFlashing} />
        </Text>
        <Text marginX={'size-50'}>|</Text>
        <Text UNSAFE_className={classes.modelInfo} data-testid={'complexity-id'}>
            Complexity: <ThreeDotsFlashing className={classes.threeDotsFlashing} />
        </Text>
    </>
);

const ModelInfoReady = ({
    modelSize,
    totalDiskSize,
    complexity,
}: {
    modelSize: string | undefined;
    totalDiskSize: string | undefined;
    complexity: number | undefined;
}) => (
    <>
        {modelSize !== undefined && (
            <>
                <Text UNSAFE_className={classes.modelInfo} data-testid={'model-size-id'}>
                    Model weight size: {modelSize}
                </Text>
                <Text marginX={'size-50'}>|</Text>
            </>
        )}
        {totalDiskSize !== undefined && (
            <>
                <Text UNSAFE_className={classes.modelInfo} data-testid={'total-disk-size-id'}>
                    Total size: {totalDiskSize}
                </Text>
                <Text marginX={'size-50'}>|</Text>
            </>
        )}
        {complexity !== undefined && (
            <Text UNSAFE_className={classes.modelInfo} data-testid={'complexity-id'}>
                Complexity: {complexity} GFlops
            </Text>
        )}
    </>
);

export const ModelInfoFields = ({
    modelSize,
    totalDiskSize,
    complexity,
    isModelTraining,
}: {
    modelSize?: string;
    totalDiskSize?: string;
    complexity?: number;
    isModelTraining: boolean;
}) => {
    return (
        <>
            {isModelTraining ? (
                <ModelInfoTraining />
            ) : (
                <ModelInfoReady modelSize={modelSize} totalDiskSize={totalDiskSize} complexity={complexity} />
            )}
        </>
    );
};
