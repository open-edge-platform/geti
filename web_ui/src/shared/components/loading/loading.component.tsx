// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';

import { LoadingIndicator } from './loading-indicator.component';

import classes from './loading.module.scss';

interface LoadingProps extends Partial<SpectrumProgressCircleProps> {
    overlay?: boolean;
    id?: string;
}

export const Loading = ({ overlay = false, id, ...rest }: LoadingProps): JSX.Element => {
    return (
        <View
            height={'100%'}
            position={'absolute'}
            left={0}
            top={0}
            right={0}
            bottom={0}
            id={id}
            data-testid={id}
            UNSAFE_className={overlay ? classes.loadingBackground : ''}
        >
            <LoadingIndicator {...rest} />
        </View>
    );
};
