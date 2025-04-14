// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
