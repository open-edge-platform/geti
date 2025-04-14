// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

interface ValidationErrorMsgProps {
    errorMsg: string;
    inheritHeight?: boolean;
    maxWidth?: string;
    gridArea?: string;
}

export const ValidationErrorMsg = ({
    errorMsg,
    inheritHeight = false,
    maxWidth,
    gridArea,
}: ValidationErrorMsgProps): JSX.Element => {
    if (isEmpty(errorMsg)) {
        return <></>;
    }

    return (
        <Flex
            alignItems={'center'}
            height={inheritHeight ? 'inherit' : 'size-300'}
            UNSAFE_style={{ fontSize: 'small', color: 'var(--brand-coral-cobalt)' }}
            maxWidth={maxWidth ?? 'inherit'}
            gridArea={gridArea}
        >
            <Text UNSAFE_style={{ whiteSpace: 'normal' }} data-testid={'label-error-message-id'}>
                {errorMsg}
            </Text>
        </Flex>
    );
};
