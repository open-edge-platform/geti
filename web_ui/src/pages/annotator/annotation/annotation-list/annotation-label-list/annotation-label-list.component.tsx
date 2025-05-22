// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment } from 'react';

import { Flex } from '@geti/ui';
import { AiIcon, CaretRightIcon } from '@geti/ui/icons';
import { isEmpty } from 'lodash-es';

import { Annotation, AnnotationLabel } from '../../../../../core/annotations/annotation.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { isPrediction, showLabelScore } from '../../../../../core/labels/utils';
import { TruncatedTextWithTooltip } from '../../../../../shared/components/truncated-text/truncated-text.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { DEFAULT_LABEL_WIDTH } from '../../labels/label.component';

import classes from './annotation-label-list.module.scss';

interface AnnotationLabelListProps {
    annotation: Annotation;
    labels: readonly Label[];
}

export const AnnotationLabelList = ({ labels, annotation }: AnnotationLabelListProps): JSX.Element => {
    const { selectedTask } = useTask();

    if (isEmpty(labels)) {
        return (
            <Fragment key={annotation.id}>
                <span>Select label</span>
            </Fragment>
        );
    }

    return (
        <Fragment key={annotation.id}>
            <ul key={`${annotation.id}-labels`} id={`${annotation.id}-labels`} className={classes.labelList}>
                {labels.map((label, labelIndex) => {
                    const annotationLabel = label as AnnotationLabel;
                    const isPredictionLabel = isPrediction(annotationLabel);
                    const hasChildren = labels.some(({ parentLabelId }) => label.id === parentLabelId);
                    const maxLabelWidth = Math.round(DEFAULT_LABEL_WIDTH / labels.length);
                    const predictionHiddenClass = annotation.isHidden ? classes.predictionHidden : '';
                    const childrenClass = hasChildren ? classes.hasChildren : '';
                    const score = isPredictionLabel ? Math.round((annotationLabel.score ?? 0) * 100) : 0;
                    const hasLabelScore = showLabelScore(annotationLabel, selectedTask?.domain);

                    return (
                        <Fragment key={`${annotation.id}-${label.id}`}>
                            <li
                                id={`${annotation.id}-labels-${label.id}`}
                                className={`${predictionHiddenClass} ${childrenClass}`}
                            >
                                {isPredictionLabel && (
                                    <Flex>
                                        <AiIcon width={10} />
                                    </Flex>
                                )}

                                <TruncatedTextWithTooltip maxWidth={maxLabelWidth}>
                                    {`${label.name}${hasLabelScore ? ` (${score}%)` : ''}`}
                                </TruncatedTextWithTooltip>

                                {hasChildren ? (
                                    <>
                                        {' '}
                                        <CaretRightIcon aria-label='inside-caret' />
                                    </>
                                ) : (
                                    <></>
                                )}
                            </li>
                            {!hasChildren && labelIndex < labels.length - 1 && (
                                <>
                                    {' '}
                                    <CaretRightIcon aria-label='outside-caret' />
                                </>
                            )}
                        </Fragment>
                    );
                })}
            </ul>
        </Fragment>
    );
};
