// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text } from '@geti/ui';

interface ArrowProps {
    isHidden?: boolean;
}

export const Arrow = ({ isHidden }: ArrowProps): JSX.Element => {
    if (isHidden) return <></>;
    return <Text marginX={'size-25'}>&#8594;</Text>;
};
