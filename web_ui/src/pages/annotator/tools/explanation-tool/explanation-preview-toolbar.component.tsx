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
