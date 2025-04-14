// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
