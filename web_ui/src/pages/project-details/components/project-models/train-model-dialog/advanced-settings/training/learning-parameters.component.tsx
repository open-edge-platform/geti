// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { noop } from 'lodash-es';

import { ConfigurableParametersParams } from '../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { Accordion } from '../ui/accordion/accordion.component';
import { Parameters } from '../ui/parameters.component';

interface LearningParametersProps {
    parameters: ConfigurableParametersParams[];
}

export const LearningParameters: FC<LearningParametersProps> = ({ parameters }) => {
    return (
        <Accordion>
            <Accordion.Title>
                Learning parameters
                <Accordion.Tag>Default</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>Specify the details of the learning process</Accordion.Description>
                <Accordion.Divider marginY={'size-250'} />
                <Parameters parameters={parameters} onChange={noop} />
            </Accordion.Content>
        </Accordion>
    );
};
