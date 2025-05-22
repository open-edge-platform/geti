// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';

interface CPStaticItemProps {
    content: string | number;
    id: string;
}

export const CPStaticItem = ({ content, id }: CPStaticItemProps): JSX.Element => {
    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            <Text id={id}>{content}</Text>
        </Flex>
    );
};
