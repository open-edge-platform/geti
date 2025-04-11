// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

import { Divider, Flex, Meter, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';

import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import {
    isBelowLowFreeDiskSpace,
    isBelowTooLowFreeDiskSpace,
    TOO_LOW_FREE_DISK_SPACE_IN_BYTES,
} from '../../../../core/status/hooks/utils';
import { ActionElement } from '../../../../shared/components/action-element/action-element.component';
import { InfoTooltip } from '../../../../shared/components/info-tooltip/info-tooltip.component';
import { getFileSize } from '../../../../shared/utils';
import { isLargeSizeQuery } from '../../../../theme/queries';

import classes from './storage-usage.module.scss';

export const StorageUsage = (): JSX.Element => {
    const { data: status } = useStatus();
    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    if (status === undefined || !isBelowLowFreeDiskSpace(status.freeSpace)) {
        return <></>;
    }

    const { freeSpace, totalSpace } = status;

    const variant = isBelowTooLowFreeDiskSpace(freeSpace)
        ? 'critical'
        : isBelowLowFreeDiskSpace(freeSpace)
          ? 'warning'
          : 'positive';

    const meterColor =
        variant === 'critical'
            ? 'var(--brand-coral-cobalt)'
            : variant === 'warning'
              ? 'var(--brand-daisy)'
              : 'var(--brand-moss)';
    const DISK_USAGE = totalSpace - freeSpace;
    const DISK_USAGE_PERCENTAGE = (DISK_USAGE / totalSpace) * 100;

    const TOOLTIP_MESSAGE =
        `${getFileSize(DISK_USAGE)} used of ${getFileSize(totalSpace)}. When the free storage hits ${getFileSize(
            TOO_LOW_FREE_DISK_SPACE_IN_BYTES
        )}, many operations such as upload media, annotation, import, etc. will not be usable. Please free up some ` +
        'space by removing unnecessary files.';

    return (
        <>
            {isLargeSize ? (
                <Flex direction={'column'} alignItems={'center'} justifyContent={'center'} gap={'size-50'}>
                    <Meter
                        variant={variant}
                        aria-label={'Storage usage'}
                        label={'Storage'}
                        value={DISK_USAGE_PERCENTAGE}
                        formatOptions={{ style: 'percent', maximumFractionDigits: 2 }}
                        UNSAFE_style={
                            {
                                '--meter-color': meterColor,
                            } as CSSProperties
                        }
                        size={'S'}
                        UNSAFE_className={classes.storageUsageMeter}
                    />
                    <Flex alignItems={'center'} gap={'size-100'} alignSelf={'start'} marginStart={'size-500'}>
                        <Text>
                            {getFileSize(DISK_USAGE)} used of {getFileSize(totalSpace)}
                        </Text>
                        <InfoTooltip id={'storage-tooltip-id'} tooltipText={TOOLTIP_MESSAGE} />
                    </Flex>
                </Flex>
            ) : (
                <TooltipTrigger placement={'bottom'}>
                    <ActionElement>
                        <Meter
                            variant={variant}
                            aria-label={'Storage usage'}
                            label={'Storage'}
                            labelPosition={'top'}
                            value={DISK_USAGE_PERCENTAGE}
                            formatOptions={{ style: 'percent', maximumFractionDigits: 2 }}
                            UNSAFE_style={
                                {
                                    '--meter-color': meterColor,
                                    cursor: 'pointer',
                                } as CSSProperties
                            }
                            width={'size-300'}
                            UNSAFE_className={classes.storageUsageMeter}
                        />
                    </ActionElement>
                    <Tooltip>{TOOLTIP_MESSAGE}</Tooltip>
                </TooltipTrigger>
            )}
            <Divider size={'S'} marginX={'size-400'} />
        </>
    );
};
