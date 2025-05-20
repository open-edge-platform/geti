// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Divider, Flex, Meter, PressableElement, Text, Tooltip, TooltipTrigger, useMediaQuery } from '@geti/ui';

import { isLargeSizeQuery } from '../../../../../packages/ui/theme/queries';
import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import {
    isBelowLowFreeDiskSpace,
    isBelowTooLowFreeDiskSpace,
    TOO_LOW_FREE_DISK_SPACE_IN_BYTES,
} from '../../../../core/status/hooks/utils';
import { InfoTooltip } from '../../../../shared/components/info-tooltip/info-tooltip.component';
import { getFileSize } from '../../../../shared/utils';

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
                    <PressableElement>
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
                    </PressableElement>
                    <Tooltip>{TOOLTIP_MESSAGE}</Tooltip>
                </TooltipTrigger>
            )}
            <Divider size={'S'} marginX={'size-400'} />
        </>
    );
};
