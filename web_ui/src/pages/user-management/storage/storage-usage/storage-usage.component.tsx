// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ColorThumb, dimensionValue, Flex, Heading, Loading, ProgressCircle, View } from '@geti/ui';
import { isNil } from 'lodash-es';

import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import { CardContent } from '../../../../shared/components/card-content/card-content.component';
import { getFileSize } from '../../../../shared/utils';

import classes from './storage-usage.module.scss';

const COLOR = `var(--energy-blue)`;

export const StorageUsage = (): JSX.Element => {
    const { data } = useStatus();

    if (isNil(data)) {
        return <Loading />;
    }

    const DISK_USAGE = data.totalSpace - data.freeSpace;
    const DISK_USAGE_PERCENTAGE = (DISK_USAGE / data.totalSpace) * 100;

    return (
        <CardContent title={'Storage usage'}>
            <View position={'relative'} marginTop={'size-200'}>
                <ProgressCircle
                    size={'L'}
                    marginX={'auto'}
                    UNSAFE_className={classes.progressGraph}
                    aria-label={`Used ${DISK_USAGE_PERCENTAGE.toFixed(0)}% of storage.`}
                    value={DISK_USAGE_PERCENTAGE}
                />
                <Flex
                    position={'absolute'}
                    UNSAFE_style={{
                        top: '0px',
                        left: '0px',
                        width: '100%',
                        height: '100%',
                        position: 'absolute',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <Heading level={4} margin={0} UNSAFE_style={{ fontSize: dimensionValue('size-450') }}>
                        {DISK_USAGE_PERCENTAGE.toFixed(0)} %
                    </Heading>
                </Flex>
            </View>

            <Flex marginTop={'size-200'} gap={'size-100'} alignItems={'center'}>
                <ColorThumb id={'progress-color'} color={COLOR} />
                {getFileSize(DISK_USAGE)} used of {getFileSize(data.totalSpace)}
            </Flex>
        </CardContent>
    );
};
