// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, ReactNode, useContext, useState } from 'react';

import isNil from 'lodash/isNil';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { isPrediction } from '../../../../core/labels/utils';
import { Task } from '../../../../core/projects/task.interface';
import { MissingProviderError } from '../../../../shared/missing-provider-error';

interface AnnotationThresholdContextProps {
    scoreThreshold: number;
    setScoreThreshold: (value: number) => void;
}

export type IsPredictionRejected = (annotation: Annotation) => boolean;

const AnnotationThresholdContext = createContext<AnnotationThresholdContextProps | undefined>(undefined);

export const AnnotationThresholdProvider = ({
    children,
    selectedTask,
    minThreshold = 0,
}: {
    children: ReactNode;
    minThreshold: number;
    selectedTask: Task | null;
}) => {
    const isAlltask = isNil(selectedTask);
    const [scoreThreshold, setScoreThreshold] = useState<number>(minThreshold);

    if (isAlltask && scoreThreshold !== 0) {
        setScoreThreshold(0);
    }

    return (
        <AnnotationThresholdContext.Provider value={{ scoreThreshold, setScoreThreshold }}>
            {children}
        </AnnotationThresholdContext.Provider>
    );
};

export const useAnnotationThreshold = (): AnnotationThresholdContextProps => {
    const context = useContext(AnnotationThresholdContext);

    if (context === undefined) {
        throw new MissingProviderError('useAnnotationThreshold', 'AnnotationThresholdProvider');
    }

    return context;
};

export const useIsPredictionRejected = (): IsPredictionRejected => {
    const { scoreThreshold } = useAnnotationThreshold();

    return (annotation: Annotation) =>
        annotation.labels.some(
            (label) => isPrediction(label) && label.score !== undefined && label.score < scoreThreshold
        );
};
