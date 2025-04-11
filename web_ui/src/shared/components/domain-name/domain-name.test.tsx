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

import { screen } from '@testing-library/react';

import { DOMAIN } from '../../../core/projects/core.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { DomainName } from './domain-name.component';

describe('DomainName', () => {
    describe('FEATURE_FLAG_ANOMALY_REDUCTION: true', () => {
        const anomalyDomains = [DOMAIN.ANOMALY_DETECTION, DOMAIN.ANOMALY_CLASSIFICATION, DOMAIN.ANOMALY_SEGMENTATION];
        it.each(anomalyDomains)(`should render Anomaly detection domain`, (domain) => {
            render(<DomainName domain={domain} />, { featureFlags: { FEATURE_FLAG_ANOMALY_REDUCTION: true } });

            expect(screen.getByText(DOMAIN.ANOMALY_DETECTION)).toBeInTheDocument();
        });

        it.each(Object.values(DOMAIN).filter((domain) => !anomalyDomains.includes(domain)))(
            'should render %s domain',
            (domain) => {
                render(<DomainName domain={domain} />, { featureFlags: { FEATURE_FLAG_ANOMALY_REDUCTION: true } });

                expect(screen.getByText(domain)).toBeInTheDocument();
            }
        );
    });

    describe('FEATURE_FLAG_ANOMALY_REDUCTION: false', () => {
        it.each(Object.values(DOMAIN))('should render %s domain', (domain) => {
            render(<DomainName domain={domain} />, { featureFlags: { FEATURE_FLAG_ANOMALY_REDUCTION: false } });

            expect(screen.getByText(domain)).toBeInTheDocument();
        });
    });
});
