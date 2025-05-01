// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { App } from './app.component';

jest.mock('@scalar/api-reference-react', () => ({
    ApiReferenceReact: () => <div>ApiReference</div>,
}));

jest.mock('react-oidc-context', () => ({
    ...jest.requireActual('react-oidc-context'),
    useAuth: () => ({
        user: {
            id_token: 'id_token',
            profile: { sub: '123' },
            expired: false,
        },
        isAuthenticated: true,
        activeNavigator: false,
        isLoading: false,
    }),
}));

describe('App component', () => {
    it('renders correctly', async () => {
        render(<App />);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        const title = await screen.findByLabelText('intel geti');

        expect(title).toBeInTheDocument();
    });
});
