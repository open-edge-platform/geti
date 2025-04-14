// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
