// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';

export interface TrainModelTemplatesProps {
    templates: SupportedAlgorithm[];
    animationDirection: number;
    selectedDomain: string;

    activeModelTemplateIdPerTask: string | undefined;

    selectedModelTemplateId: string;
    handleSelectedTemplateId: (modelTemplateId: string | null) => void;
}
