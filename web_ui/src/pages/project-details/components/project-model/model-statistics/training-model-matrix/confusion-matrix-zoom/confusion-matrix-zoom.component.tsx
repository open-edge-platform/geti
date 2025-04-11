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

import { TransformComponent, TransformWrapper } from 'react-zoom-pan-pinch';

import { ConfusionMatrix } from '../../../../../../../shared/components/charts/confusion-matrix/confusion-matrix.component';
import { ConfusionMatrixProps } from '../../../../../../../shared/components/charts/confusion-matrix/confusion-matrix.interface';
import { withDownloadableHtml } from '../../../../../../../shared/components/download-graph-menu/with-downloadable-svg.hoc';

import classes from './confusion-matrix.module.scss';

interface ConfusionMatrixZoomProps extends ConfusionMatrixProps {
    size: number;
    title: string;
}

const fitConfusionMatrixSize = 3;

const DownloadableConfusionMatrix = withDownloadableHtml(ConfusionMatrix);

export const ConfusionMatrixZoom = ({ size, ...rest }: ConfusionMatrixZoomProps): JSX.Element => {
    const disablePanningAndZoom = size <= fitConfusionMatrixSize;

    return (
        <TransformWrapper panning={{ disabled: disablePanningAndZoom }} disabled={disablePanningAndZoom}>
            <TransformComponent wrapperClass={classes.transformWrapper} contentClass={classes.transformContent}>
                <DownloadableConfusionMatrix size={size} {...rest} />
            </TransformComponent>
        </TransformWrapper>
    );
};
