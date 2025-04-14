// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { DOMAIN } from '../../../core/projects/core.interface';
import { isAnomalyDomain } from '../../../core/projects/domains';

interface DomainNameProps {
    domain: DOMAIN;
}

export const DomainName = ({ domain }: DomainNameProps): JSX.Element => {
    const { FEATURE_FLAG_ANOMALY_REDUCTION } = useFeatureFlags();

    if (FEATURE_FLAG_ANOMALY_REDUCTION && isAnomalyDomain(domain)) {
        return <>{DOMAIN.ANOMALY_DETECTION}</>;
    }

    return <>{domain}</>;
};
