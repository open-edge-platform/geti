// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
