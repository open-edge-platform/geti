// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DimensionValue, Flex, ProgressCircle } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';
import { Responsive } from '@react-types/shared';

interface LoadingIndicatorProps extends SpectrumProgressCircleProps {
    height?: Responsive<DimensionValue>;
}
export const LoadingIndicator = (props: LoadingIndicatorProps): JSX.Element => {
    const { size = 'L', height = '100%', ...rest } = props;

    return (
        <Flex alignItems={'center'} justifyContent={'center'} height={height}>
            <ProgressCircle aria-label={'Loading...'} isIndeterminate size={size} {...rest} />
        </Flex>
    );
};
