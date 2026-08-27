// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, Suspense, useState } from 'react';

import { Flex, Item, Loading, TabList, TabPanels, Tabs, Text, View } from '@geti-ui/ui';

import { ConfidenceThreshold } from '../../../components/confidence-threshold/confidence-threshold.component';
import { FEATURE_FLAGS } from '../../../constants/feature-flags';
import { SinkActions } from '../sinks/sink-actions.component';
import { SourceActions } from '../sources/source-actions.component';
import { StreamInferenceDevices } from './stream-inference-devices.component';

const ConfigurationItem = ({ children }: { children: ReactNode }) => {
    return (
        <View position={'relative'} minHeight={'size-800'}>
            <Suspense fallback={<Loading mode={'inline'} size={'M'} />}>{children}</Suspense>
        </View>
    );
};

// TODO: read the value from `inference.confidence_threshold` and persist it through `PATCH /pipeline`
const PipelineConfidenceThreshold = () => {
    const FALLBACK_CONFIDENCE_THRESHOLD = 0.3;
    const [threshold, setThreshold] = useState(FALLBACK_CONFIDENCE_THRESHOLD);

    return (
        <ConfidenceThreshold value={threshold} defaultValue={FALLBACK_CONFIDENCE_THRESHOLD} onChange={setThreshold} />
    );
};

export const PipelineConfiguration = () => {
    return (
        <Flex direction={'column'} gap={'size-150'} minHeight={0}>
            <Suspense fallback={<Loading />}>
                <StreamInferenceDevices />
            </Suspense>

            {FEATURE_FLAGS.CONFIDENCE_THRESHOLD && <PipelineConfidenceThreshold />}

            <Tabs
                aria-label={'Pipeline configuration tabs'}
                flex={1}
                minHeight={0}
                UNSAFE_style={{
                    '--spectrum-tabs-selection-indicator-color': 'var(--energy-blue)',
                }}
            >
                <TabList marginBottom={'size-200'}>
                    <Item key='sources' textValue='Sources'>
                        <Text>Input</Text>
                    </Item>
                    <Item key='sinks' textValue='Sinks'>
                        <Text>Output</Text>
                    </Item>
                </TabList>
                <TabPanels flex={1} minHeight={0} UNSAFE_style={{ overflowY: 'auto' }}>
                    <Item key='sources'>
                        <ConfigurationItem>
                            <SourceActions />
                        </ConfigurationItem>
                    </Item>
                    <Item key='sinks'>
                        <ConfigurationItem>
                            <SinkActions />
                        </ConfigurationItem>
                    </Item>
                </TabPanels>
            </Tabs>
        </Flex>
    );
};
