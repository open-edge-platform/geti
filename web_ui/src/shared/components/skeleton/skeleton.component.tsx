// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { AriaLabelingProps, DOMProps, StyleProps } from '@react-types/shared';
import { clsx } from 'clsx';

import classes from './skeleton.module.scss';

interface SkeletonProps extends DOMProps, StyleProps, AriaLabelingProps {
    isCircle?: boolean;
    isAspectRatioOne?: boolean;
}

export const Skeleton = (props: SkeletonProps): JSX.Element => {
    const { isCircle, isAspectRatioOne = false, ...rest } = props;

    return (
        <View
            {...rest}
            UNSAFE_className={clsx(classes.skeleton, rest.UNSAFE_className, {
                [classes.circle]: isCircle,
                [classes.aspectRatio]: isAspectRatioOne,
            })}
        />
    );
};
