// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import { Switch } from '@geti/ui';

import { Accordion } from '../../ui/accordion/accordion.component';
import { Tooltip } from '../../ui/tooltip.component';

const RemovingDuplicatesTooltip: FC = () => {
    return (
        <Tooltip>
            Enable this option to automatically detect and remove duplicate media items from your dataset. This helps to
            ensure that your model is trained on unique and diverse data, improving its accuracy and performance.
        </Tooltip>
    );
};

/*
 * This component is currently not used in the v1 of Training flow revamp. Will be used in the later version.
 */
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
