// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { ConfigurableParametersParams } from '../../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { Accordion } from '../../accordion/accordion.component';

interface LearningParametersOptionsProps {
    parameters: ConfigurableParametersParams[];
}

const LearningParametersOptions: FC<LearningParametersOptionsProps> = ({ parameters }) => {
    return (
        <>
            {parameters.map((parameter) => {
                return <></>;
            })}
        </>
    );
};

interface LearningParametersProps {
    parameters: ConfigurableParametersParams[];
}

export const LearningParameters: FC<LearningParametersProps> = ({ parameters }) => {
    console.log({ parameters });

    return (
        <Accordion>
            <Accordion.Title>
                Learning parameters
                <Accordion.Tag>Default</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>Specify the details of the learning process</Accordion.Description>
                <Accordion.Divider marginY={'size-250'} />
                <LearningParametersOptions parameters={parameters} />
            </Accordion.Content>
        </Accordion>
    );
};
