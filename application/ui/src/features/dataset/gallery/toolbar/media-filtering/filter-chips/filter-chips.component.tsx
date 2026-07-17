// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Flex, Text } from '@geti-ui/ui';
import { BorderClose } from '@geti-ui/ui/icons';

import classes from './filter-chips.module.scss';

type FilterChipsProps = {
    name: string;
    onClose: () => void;
};

export const FilterChips = ({ name, onClose }: FilterChipsProps) => {
    return (
        <Flex UNSAFE_className={classes.container} alignItems={'center'}>
            <Text>{name}</Text>

            <ActionButton
                UNSAFE_className={classes.closeIcon}
                isQuiet
                aria-label={`Remove ${name} filter`}
                onPress={onClose}
            >
                <BorderClose
                    width={'var(--spectrum-global-dimension-size-175)'}
                    height={'var(--spectrum-global-dimension-size-175)'}
                />
            </ActionButton>
        </Flex>
    );
};
