// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
