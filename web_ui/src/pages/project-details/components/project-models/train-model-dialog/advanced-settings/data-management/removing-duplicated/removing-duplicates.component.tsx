// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Content, ContextualHelp, Flex, Text } from '@adobe/react-spectrum';

import { Switch } from '../../../../../../../../shared/components/switch/switch.component';
import { Accordion } from '../../ui/accordion/accordion.component';

const RemovingDuplicatesTooltip: FC = () => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>
                    Enable this option to automatically detect and remove duplicate media items from your dataset. This
                    helps to ensure that your model is trained on unique and diverse data, improving its accuracy and
                    performance.
                </Text>
            </Content>
        </ContextualHelp>
    );
};

export const RemovingDuplicates: FC = () => {
    const [isRemovingDuplicatesEnabled, setIsRemovingDuplicatesEnabled] = useState<boolean>(false);

    return (
        <Accordion>
            <Accordion.Title>
                Removing duplicates <Accordion.Tag>{isRemovingDuplicatesEnabled ? 'On' : 'Off'}</Accordion.Tag>
                <Accordion.Warning>Recommended On</Accordion.Warning>
            </Accordion.Title>
            <Accordion.Content>
                <Flex alignItems={'center'} gap={'size-600'}>
                    <Text>
                        Removing duplicates <RemovingDuplicatesTooltip />
                    </Text>
                    <Switch
                        isEmphasized
                        aria-label={`${isRemovingDuplicatesEnabled ? 'Enabled' : 'Disabled'} removing duplicates`}
                        isSelected={isRemovingDuplicatesEnabled}
                        onChange={setIsRemovingDuplicatesEnabled}
                    >
                        {isRemovingDuplicatesEnabled ? 'On' : 'Off'}
                    </Switch>
                </Flex>
                <Accordion.Description>
                    We recommend removing duplicates to avoid wasting resources on training.
                </Accordion.Description>
            </Accordion.Content>
        </Accordion>
    );
};
