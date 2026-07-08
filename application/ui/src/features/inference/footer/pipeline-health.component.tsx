// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Content, ContextualHelp, Flex, StatusLight, Text } from '@geti-ui/ui';
import { usePipelineHealth } from 'hooks/api/pipeline.hook';

import { PipelineComponentsHealth } from '../../../constants/shared-types';
import { getComponentStatusMeta, getOverallStatusMeta, hasComponentMessage } from './utils';

const COMPONENT_ORDER = ['source', 'sink', 'model'] as const;

const COMPONENT_LABELS: Record<(typeof COMPONENT_ORDER)[number], string> = {
    source: 'Source',
    sink: 'Sink',
    model: 'Model',
};

interface PipelineComponentsHelpProps {
    components: PipelineComponentsHealth;
}

const PipelineComponentsHelp = ({ components }: PipelineComponentsHelpProps) => {
    return (
        <ContextualHelp variant={'info'} aria-label={'Pipeline component health'}>
            <Content>
                <Flex direction={'column'} gap={'size-100'}>
                    {COMPONENT_ORDER.map((key) => {
                        const { label, variant } = getComponentStatusMeta(components[key]);

                        return (
                            <Flex key={key} alignItems={'center'} gap={'size-100'}>
                                <Text>{COMPONENT_LABELS[key]}</Text>
                                <StatusLight variant={variant}>{label}</StatusLight>
                            </Flex>
                        );
                    })}
                </Flex>
            </Content>
        </ContextualHelp>
    );
};

export const PipelineHealth = () => {
    const { data, isPending, isError } = usePipelineHealth();

    if (isPending || isError) {
        return null;
    }

    const { label, variant } = getOverallStatusMeta(data.status);
    const components = data.components;
    const showComponentsHelp = components != null && hasComponentMessage(components);

    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            <StatusLight role={'status'} variant={variant}>
                {label}
            </StatusLight>

            {showComponentsHelp && <PipelineComponentsHelp components={components} />}
        </Flex>
    );
};
