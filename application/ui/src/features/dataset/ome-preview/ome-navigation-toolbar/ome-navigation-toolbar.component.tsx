// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { AnnotatedOmePlane, MediaOmePlane, OmeImageInfo } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Divider, Flex, Slider, Text, View } from '@geti-ui/ui';

import { Toolbar } from '../../../../modules/annotator/shell/toolbar-container/toolbar-container.component';
import { OmeChannelsButton } from '../ome-channels/ome-channels-button.component';
import { OmeMetadataButton } from './ome-metadata-button.component';

import classes from './ome-navigation-toolbar.module.scss';

type PlaneSliderProps = {
    label: string;
    value: number;
    count: number;
    annotatedIndexes: number[];
    onChange: (value: number) => void;
};

// Slider over one plane axis, marking the indexes that hold annotated planes
const PlaneSlider = ({ label, value, count, annotatedIndexes, onChange }: PlaneSliderProps) => {
    const [draftValue, setDraftValue] = useState<number | null>(null);
    const maxValue = Math.max(count - 1, 1);

    return (
        <View position={'relative'} flex={1} minWidth={'size-2400'}>
            <Slider
                label={label}
                width={'100%'}
                minValue={0}
                maxValue={maxValue}
                step={1}
                value={draftValue ?? value}
                isDisabled={count <= 1}
                onChange={setDraftValue}
                onChangeEnd={(newValue) => {
                    setDraftValue(null);
                    onChange(newValue);
                }}
                getValueLabel={(current) => `${current + 1} / ${count}`}
            />
            <div className={classes.markers} aria-hidden>
                {annotatedIndexes.map((index) => (
                    <span key={index} className={classes.marker} style={{ left: `${(index / maxValue) * 100}%` }} />
                ))}
            </div>
        </View>
    );
};

type OmeNavigationToolbarProps = {
    info: OmeImageInfo;
    plane: MediaOmePlane;
    annotatedPlanes: AnnotatedOmePlane[];
    onSelectPlane: (z: number, t: number) => void;
};

export const OmeNavigationToolbar = ({ info, plane, annotatedPlanes, onSelectPlane }: OmeNavigationToolbarProps) => {
    const { t } = useTranslation();

    // Markers along an axis show the annotated planes reachable by moving along that axis only
    const annotatedZ = annotatedPlanes.filter((p) => p.t_index === plane.t_index).map((p) => p.z_index);
    const annotatedT = annotatedPlanes.filter((p) => p.z_index === plane.z_index).map((p) => p.t_index);

    return (
        <Toolbar.Container>
            <Toolbar.Section>
                <View paddingX={'size-100'}>
                    <Flex alignItems={'center'} gap={'size-300'} wrap>
                        <PlaneSlider
                            label={t('annotator.ome.zSlice')}
                            value={plane.z_index}
                            count={info.size_z}
                            annotatedIndexes={annotatedZ}
                            onChange={(z) => onSelectPlane(z, plane.t_index)}
                        />
                        <PlaneSlider
                            label={t('annotator.ome.timePoint')}
                            value={plane.t_index}
                            count={info.size_t}
                            annotatedIndexes={annotatedT}
                            onChange={(timePoint) => onSelectPlane(plane.z_index, timePoint)}
                        />

                        <Divider orientation={'vertical'} size={'S'} />

                        <Text>{t('annotator.ome.annotatedPlanes', { count: annotatedPlanes.length })}</Text>

                        <OmeChannelsButton mediaId={plane.id} info={info} />
                        <OmeMetadataButton info={info} />
                    </Flex>
                </View>
            </Toolbar.Section>
        </Toolbar.Container>
    );
};
