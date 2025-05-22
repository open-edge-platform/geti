// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Heading, Meter, Text, View } from '@geti/ui';
import { countBy, identity } from 'lodash-es';

import { Label } from '../../../../core/labels/label.interface';
import { isNonEmptyArray } from '../../../../shared/utils';
import { Screenshot } from '../../../camera-support/camera.interface';
import { DeviceSettings } from './device-settings.component';
import { SidebarThumbnail } from './sidebar-thumbnail.component';

import classes from './sidebar.module.scss';

interface OpenSidebarProps {
    labels: Label[];
    screenshots: Screenshot[];
    isLivePrediction: boolean;
}

export const OpenSidebar = ({ labels, screenshots, isLivePrediction }: OpenSidebarProps): JSX.Element => {
    const allLabelIds = screenshots.flatMap((screenshot) => screenshot.labelIds);
    const countedLabels = countBy(allLabelIds, identity);

    return (
        <View padding={'size-250'} overflow={'auto'}>
            <SidebarThumbnail screenshots={screenshots} />
            <Divider size={'S'} />

            {isNonEmptyArray(labels) && !isLivePrediction && (
                <>
                    <Heading level={3}>Images</Heading>
                    <View
                        UNSAFE_style={{ overflow: 'auto' }}
                        height={'size-1700'}
                        paddingEnd={'size-100'}
                        marginBottom={'size-200'}
                    >
                        {labels.map((label) => {
                            const total = countedLabels[label.id] ?? 0;

                            return (
                                <Meter
                                    key={label.id}
                                    variant={'positive'}
                                    value={total}
                                    label={label.name}
                                    valueLabel={String(total)}
                                    UNSAFE_className={classes.annotationMeter}
                                />
                            );
                        })}
                    </View>

                    <Flex marginBottom={'size-200'} width={'100%'} direction={'row'}>
                        <View width={'50%'}>
                            <Text>All</Text>
                        </View>
                        <View UNSAFE_style={{ textAlign: 'end' }} width={'50%'}>
                            <Text>{screenshots.length}</Text>
                        </View>
                    </Flex>
                    <Divider size={'S'} />
                </>
            )}

            <DeviceSettings />
        </View>
    );
};
