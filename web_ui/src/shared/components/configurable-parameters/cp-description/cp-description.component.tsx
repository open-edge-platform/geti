// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex } from '@geti/ui';

interface CPDescriptionProps {
    description: string;
    id: string;
}

export const CPDescription = ({ description, id }: CPDescriptionProps): JSX.Element => {
    return (
        <>
            <Flex marginY={'size-100'} id={id}>
                {description}
            </Flex>
            <Divider size={'S'} marginBottom={'size-250'} />
        </>
    );
};
