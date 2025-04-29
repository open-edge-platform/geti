// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { WelcomingCreditsDetails } from './welcoming-credits-details.component';

describe('WelcomingCreditsDetails', () => {
    it('should render welcoming credits details with correct values', async () => {
        const initAmount = 5000;
        const renewableAmount = 1000;

        render(<WelcomingCreditsDetails initCredits={initAmount} monthlyRenewalCredits={renewableAmount} />);

        expect(screen.getByTestId(`init-credits-${initAmount}-id`)).toBeInTheDocument();
        expect(screen.getByTestId(`renewable-credits-${renewableAmount}-id`)).toBeInTheDocument();
    });

    it('should not render renewable amount if it is not defined', async () => {
        const initAmount = 5000;
        const renewableAmount = 1000;

        render(<WelcomingCreditsDetails initCredits={initAmount} monthlyRenewalCredits={null} />);

        expect(screen.getByTestId(`init-credits-${initAmount}-id`)).toBeInTheDocument();
        expect(screen.queryByTestId(`renewable-credits-${renewableAmount}-id`)).not.toBeInTheDocument();
    });
});
