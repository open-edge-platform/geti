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

import { useMemo } from 'react';

import { Flex, Heading, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import noop from 'lodash/noop';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { fetchLabelsTree } from '../../../../../core/labels/annotator-utils/labels-utils';
import { getNonEmptyLabelsFromProject } from '../../../../../core/labels/utils';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { usePrediction } from '../../../providers/prediction-provider/prediction-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { ToolAnnotationContextProps } from '../../../tools/tools.interface';
import { SearchLabelTreeView } from '../../labels/label-search/search-label-tree-view.component';

import classes from './annotations.module.scss';

const ALL_COUNTS = 'sum';
const NO_LABEL = 'no-label';

// Loop through all the annotations and their labels,
// to get the total count of annotations containing a specific label
const getAnnotationsCountPerLabel = (annotations: readonly Annotation[]): Map<string, number> => {
    const counter = new Map<string, number>([]);
    counter.set(ALL_COUNTS, 0);

    annotations.forEach((annotation) => {
        if (isEmpty(annotation.labels)) {
            if (counter.has(NO_LABEL)) {
                const prevNoLabelCount = counter.get(NO_LABEL) ?? 0;
                counter.set(NO_LABEL, prevNoLabelCount + 1);
            } else {
                counter.set(NO_LABEL, 1);
            }

            return;
        }

        annotation.labels.forEach(({ name }) => {
            const prevCount = counter.get(name) ?? 0;
            counter.set(name, prevCount + 1);

            const prevAllCount = counter.get(ALL_COUNTS) ?? 0;
            counter.set(ALL_COUNTS, prevAllCount + 1);
        });
    });

    return counter;
};

const useAnnotations = (annotationToolContext: AnnotationToolContext) => {
    const {
        scene: { annotations },
    } = annotationToolContext;
    const { predictionAnnotations } = usePrediction();
    const { isActiveLearningMode } = useAnnotatorMode();

    return isActiveLearningMode ? annotations : predictionAnnotations;
};

export const AnnotationListCounting = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const annotations = useAnnotations(annotationToolContext);

    const { tasks } = useTask();
    const userDefinedLabels = getNonEmptyLabelsFromProject(tasks);
    const labels = fetchLabelsTree(userDefinedLabels);
    const labelsCount = useMemo(() => getAnnotationsCountPerLabel(annotations), [annotations]);

    const hasNoLabels = Boolean(labelsCount.get(NO_LABEL));

    return (
        <View data-testid='annotation-counting-list' UNSAFE_className={classes.countingList}>
            <View UNSAFE_className={classes.multipleLabelWrapper} padding={'size-150'}>
                <Flex alignItems={'center'} justifyContent={'space-between'}>
                    <Heading level={4}>Counting</Heading>

                    <Text data-testid='all-labels-count-id' marginEnd={'size-200'}>
                        {labelsCount.get(ALL_COUNTS)}
                    </Text>
                </Flex>

                <View UNSAFE_className={classes.labelTreeWrapper}>
                    {hasNoLabels && (
                        <Flex
                            marginX={'size-200'}
                            height={'size-300'}
                            justifyContent={'space-between'}
                            alignItems={'center'}
                            aria-label={`annotation label count no label`}
                        >
                            <Text>No label</Text>
                            <Text>{labelsCount.get(NO_LABEL) ?? 0}</Text>
                        </Flex>
                    )}
                    <SearchLabelTreeView
                        labels={labels}
                        itemClickHandler={noop}
                        suffix={(label) => {
                            return (
                                <span aria-label={`annotation label count ${label.id}`}>
                                    {labelsCount.get(label.name) ?? 0}
                                </span>
                            );
                        }}
                    />
                </View>
            </View>
        </View>
    );
};
