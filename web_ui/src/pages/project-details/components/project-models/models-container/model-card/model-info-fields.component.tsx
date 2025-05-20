import { Text } from '@adobe/react-spectrum';

import { ThreeDotsFlashing } from '../../../../../../shared/components/three-dots-flashing/three-dots-flashing.component';

import classes from './model-card.module.scss';

export const ModelInfoFields = ({
    modelSize,
    totalDiskSize,
    complexity,
    isModelDeleted,
}: {
    modelSize: string | undefined;
    totalDiskSize: string | undefined;
    complexity: number | undefined;
    isModelDeleted: boolean;
}) => {
    return (
        <>
            {!isModelDeleted && (
                <>
                    <Text UNSAFE_className={classes.modelInfo} data-testid={'model-size-id'}>
                        Model size: {modelSize ?? <ThreeDotsFlashing className={classes.threeDotsFlashing} />}
                    </Text>
                    <Text marginX={'size-50'}>|</Text>
                    <Text UNSAFE_className={classes.modelInfo} data-testid={'total-disk-size-id'}>
                        Total size:{' '}
                        {totalDiskSize === '0' ? (
                            <ThreeDotsFlashing className={classes.threeDotsFlashing} />
                        ) : (
                            totalDiskSize
                        )}
                    </Text>
                    <Text marginX={'size-50'}>|</Text>
                </>
            )}
            <Text UNSAFE_className={classes.modelInfo} data-testid={'complexity-id'}>
                Complexity:{' '}
                {complexity ? (
                    <span>{complexity} GFlops</span>
                ) : (
                    <ThreeDotsFlashing className={classes.threeDotsFlashing} />
                )}
            </Text>
        </>
    );
};
