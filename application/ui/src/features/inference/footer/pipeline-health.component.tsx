// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Fragment } from 'react';

import {
    ActionButton,
    Content,
    Dialog,
    DialogTrigger,
    dimensionValue,
    Flex,
    Grid,
    StatusLight,
    Text,
} from '@geti-ui/ui';
import { InfoOutline } from '@geti-ui/ui/icons';
import { usePipelineHealth } from 'hooks/api/pipeline.hook';

import { PipelineComponentsHealth } from '../../../constants/shared-types';
import { getComponentStatusMeta, getOverallStatusMeta, shouldShowPipelineHealthDetails } from './utils';

const COMPONENT_ORDER = ['source', 'sink', 'model'] as const;

const COMPONENT_LABELS: Record<(typeof COMPONENT_ORDER)[number], string> = {
    source: 'Source',
    sink: 'Sink',
    model: 'Model',
};

interface PipelineComponentsDetailsInfoProps {
    components: PipelineComponentsHealth;
}

const PipelineComponentsDetailsInfo = ({ components }: PipelineComponentsDetailsInfoProps) => {
    return (
        <DialogTrigger type={'popover'} placement={'top'}>
            <ActionButton isQuiet aria-label={'Pipeline component health'}>
                <InfoOutline />
            </ActionButton>
            <Dialog>
                <Content>
                    <Grid gap={'size-50'} columns={['max-content', 'max-content', 'auto']} alignContent={'start'}>
                        {COMPONENT_ORDER.map((key) => {
                            const { label, variant, message } = getComponentStatusMeta(components[key]);

                            return (
                                <Fragment key={key}>
                                    <Text>{COMPONENT_LABELS[key]}</Text>
                                    <StatusLight
                                        variant={variant}
                                        UNSAFE_style={{ padding: 0, paddingRight: dimensionValue('size-50') }}
                                    >
                                        {label}
                                    </StatusLight>
                                    <Text marginStart={'size-150'}>{message}</Text>
                                </Fragment>
                            );
                        })}
                    </Grid>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};

export const PipelineHealth = () => {
    const { data, isPending, isError } = usePipelineHealth();

    if (isPending || isError) {
        return null;
    }

    const { label, variant } = getOverallStatusMeta(data.status);
    const components = data.components;
    const showPipelineHealthDetails = components != null && shouldShowPipelineHealthDetails(components);

    return (
        <Flex alignItems={'center'} gap={'size-100'} height={'100%'}>
            <StatusLight role='status' variant={variant} UNSAFE_style={{ padding: 0, alignItems: 'center' }}>
                {label}
            </StatusLight>

            {showPipelineHealthDetails && <PipelineComponentsDetailsInfo components={components} />}
        </Flex>
    );
};
