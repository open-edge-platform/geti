// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Heading, ProgressCircle, View } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import isNil from 'lodash/isNil';

import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import { CardContent } from '../../../../shared/components/card-content/card-content.component';
import { ColorThumb } from '../../../../shared/components/color-thumb/color-thumb.component';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { getFileSize } from '../../../../shared/utils';

import classes from './storage-usage.module.scss';

const COLOR = `var(--energy-blue)`;

export const StorageUsage = (): JSX.Element => {
    const { data } = useStatus();

    if (isNil(data)) {
        return <Loading id={'storage-usage-loading-id'} />;
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
