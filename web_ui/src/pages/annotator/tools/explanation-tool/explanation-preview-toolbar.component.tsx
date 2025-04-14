// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Explanation } from '../../../../core/annotations/prediction.interface';
import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';
import { ExplanationToolbar } from './explanation-toolbar.component';

export interface ExplanationPreviewToolbarProps {
    explanations: Explanation[];
    selectedExplanation?: Explanation;
}

export const ExplanationPreviewToolbar = ({
    explanations,
    selectedExplanation,
}: ExplanationPreviewToolbarProps): JSX.Element => {
    const { setSelectedExplanation } = usePrediction();

    useEffect(() => {
        if (selectedExplanation) {
            setSelectedExplanation(selectedExplanation);
        }
    }, [selectedExplanation, setSelectedExplanation]);

    return <ExplanationToolbar explanations={explanations} />;
};
