// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../../../core/projects/core.interface';

export interface DomainStepProps {
    domains: DOMAIN[];
    handleSelection: (domain: DOMAIN) => void;
    selected?: DOMAIN;
    isValid: boolean;
}
