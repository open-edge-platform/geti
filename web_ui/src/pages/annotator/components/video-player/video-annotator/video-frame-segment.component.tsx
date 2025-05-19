// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, useNumberFormatter, View } from '@geti/ui';

import { Label } from '../../../../../core/labels/label.interface';
import { useVideoTimelineQueries } from '../hooks/use-video-timeline-queries.hook';

import classes from './video-annotator.module.scss';

const SelectedFrameOverlay = (): JSX.Element => {
    return (
        <View
            data-testid='selected'
            top={0}
            left={0}
            right={0}
            bottom={0}
            backgroundColor='static-white'
            position='absolute'
            UNSAFE_className={classes.activeFrameOverlay}
        />
    );
};
const ActiveFrameOverlay = (): JSX.Element => {
    return <View data-testid='active' UNSAFE_className={classes.activeFrame} />;
};

const getAriaLabel = (label: Label | undefined, isPrediction: boolean) => {
    if (isPrediction) {
        if (label === undefined) {
            return 'No prediction';
        }
        return `Predicted ${label.name}`;
    }

    if (label === undefined) {
        return 'No label';
    }
    return label.name;
};

interface LabelSegmentProps {
    label?: Label;
    striped: boolean;
    isLoading: boolean;
    isPrediction?: boolean;
}
const LabelSegment = ({ label, striped, isLoading, isPrediction = false }: LabelSegmentProps): JSX.Element => {
    if (isLoading) {
        return <View width='100%' height='size-100' UNSAFE_className={classes.loadingGradient} />;
    }

    const backgroundColor =
        label !== undefined ? label.color : striped ? 'var(--spectrum-global-color-gray-400)' : undefined;

    return (
        <div aria-label={getAriaLabel(label, isPrediction)} role='presentation'>
            <View
                width='100%'
                height='size-100'
                UNSAFE_className={`${classes.labelMarker} ${striped ? classes.stripedBackground : ''}`}
                UNSAFE_style={{ backgroundColor }}
            />
        </div>
    );
};

interface VideoFrameSegmentProps {
    isSelectedFrame: boolean;
    isActiveFrame: boolean;
    isFilteredFrame: boolean;
    labels: readonly Label[];
    onClick: (frameNumber: number) => void;
    frameNumber: number;
    showTicks: boolean;
    colIndex: number;
    isLastFrame: boolean;
    isFirstFrame: boolean;
}

export const VideoFrameSegment = ({
    isSelectedFrame,
    isActiveFrame,
    isFilteredFrame,
    labels,
    onClick,
    frameNumber,
    showTicks,
    colIndex,
    isLastFrame,
    isFirstFrame,
}: VideoFrameSegmentProps): JSX.Element => {
    const { annotationsQuery, predictionsQuery } = useVideoTimelineQueries(frameNumber);
    const annotatedLabels = annotationsQuery.data ?? new Set<string>();
    const predictedLabels = predictionsQuery.data ?? new Set<string>();

    const formatter = useNumberFormatter({
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
        maximumSignificantDigits: 4,
        notation: 'compact',
    });

    const tickTextStyle = {
        left: isFirstFrame ? '50%' : 'initial',
        right: isLastFrame ? '0' : 'initial',
    };

    return (
        <div onClick={() => onClick(frameNumber)} className={classes.videoFrameSegment} role='group'>
            <div
                className={classes.ticks}
                role='columnheader'
                id={`frame-${colIndex + 1}`}
                aria-label={`frame number ${frameNumber}`}
            >
                {showTicks ? (
                    <div className={classes.ticksText} style={tickTextStyle}>
                        {formatter.format(frameNumber)}f
                        <div className={classes.ticksIndicator} />
                    </div>
                ) : (
                    <></>
                )}
            </div>

            {isActiveFrame || isFilteredFrame ? <ActiveFrameOverlay /> : <></>}
            {isSelectedFrame ? <SelectedFrameOverlay /> : <></>}

            <Flex
                gap='size-100'
                direction='column'
                marginTop='size-100'
                UNSAFE_className={isFilteredFrame ? classes.filteredFrame : ''}
            >
                {labels.map((label, rowIndex) => {
                    return (
                        <div
                            role='gridcell'
                            key={label.id}
                            aria-colindex={colIndex + 1}
                            aria-rowindex={rowIndex + 1}
                            aria-label={`Label ${label.name} in frame number ${frameNumber}`}
                        >
                            <Flex gap='size-10' height='size-225' direction='column' marginEnd={'size-10'}>
                                <LabelSegment
                                    striped={false}
                                    isLoading={annotationsQuery.isLoading}
                                    label={annotatedLabels.has(label.id) ? label : undefined}
                                />
                                <LabelSegment
                                    isPrediction
                                    striped={true}
                                    isLoading={predictionsQuery.isLoading}
                                    label={predictedLabels.has(label.id) ? label : undefined}
                                />
                            </Flex>
                        </div>
                    );
                })}
            </Flex>
        </div>
    );
};
