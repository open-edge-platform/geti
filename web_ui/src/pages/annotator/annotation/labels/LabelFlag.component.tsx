// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import isEmpty from 'lodash/isEmpty';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Circle } from '../../../../core/annotations/shapes.interface';
import { isCircle, isRect } from '../../../../core/annotations/utils';

import classes from './labels.module.scss';

interface LabelFlagProps {
    y: number;
    top: number;
    left: number;
    annotation: Annotation;
}

const getHeight = (annotation: Annotation, top: number, y: number) => {
    const getFlagFromTop = (shape: Circle) => y - shape.r - top;

    return isCircle(annotation.shape) ? getFlagFromTop(annotation.shape) : y - top;
};

export const LabelFlag = ({ annotation, top, left, y }: LabelFlagProps): JSX.Element => {
    const { shape } = annotation;

    if (isRect(shape)) {
        return <></>;
    }

    const labels = [...annotation.labels];

    const height = getHeight(annotation, top, y);
    const color = isEmpty(labels) ? 'var(--spectrum-global-color-gray-50)' : labels.at(-1)?.color;

    return (
        <div
            className={classes.labelFlag}
            style={{
                top,
                left,
                height,
                backgroundColor: color,
                opacity: 'var(--label-opacity)',
            }}
        />
    );
};
