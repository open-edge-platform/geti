// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { darkTheme, Provider } from '@adobe/react-spectrum';
import { render, screen } from '@testing-library/react';

import { Loading } from './loading.component';

const TestProvider = ({ children }: { children: ReactNode }) => {
    return <Provider theme={darkTheme}>{children}</Provider>;
};

describe('Loading', () => {
    const renderLoading = (props = {}) => {
        return render(
            <TestProvider>
                <Loading {...props} />
            </TestProvider>
        );
    };

    describe('inline mode', () => {
        it('renders inline loading spinner without overlay', () => {
            renderLoading({ mode: 'inline' });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();
            expect(progressbar).toHaveAttribute('aria-label', 'Loading...');

            // In inline mode, there should be no overlay containers
            const positionContainer = progressbar.closest('[style*="position: absolute"]');
            const classContainer = progressbar.closest('[class*="overlay"]');
            expect(positionContainer).not.toBeInTheDocument();
            expect(classContainer).not.toBeInTheDocument();
        });

        it('supports custom props and styling in inline mode', () => {
            renderLoading({
                mode: 'inline',
                size: 'S',
                style: {
                    height: '150px',
                },
                'aria-label': 'Custom loading message',
                value: 50,
            });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toHaveAttribute('aria-label', 'Custom loading message');
            expect(progressbar).toHaveAttribute('aria-valuemax', '100');

            // Check spinner container height
            const flexContainer = progressbar.parentElement;
            expect(flexContainer).toHaveStyle({ height: '150px' });
        });
    });

    describe('fullscreen mode', () => {
        it('renders with default styling and overlay', () => {
            renderLoading(); // Default mode is fullscreen

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();
            expect(progressbar).toHaveAttribute('aria-label', 'Loading...');

            // Should render overlay container with CSS classes and default background
            const container = progressbar.parentElement;
            expect(container).toBeInTheDocument();
            expect(container).toHaveClass('overlay', 'fullscreen');
            expect(container).toHaveStyle({ backgroundColor: 'var(--spectrum-global-color-gray-50)' });
        });

        it('supports custom styling and spinner height', () => {
            renderLoading({
                mode: 'fullscreen',
                className: 'custom-loading-class',
                style: {
                    backgroundColor: 'rgba(255, 0, 0, 0.5)',
                    left: 10,
                    right: 20,
                    top: 30,
                    bottom: 40,
                    paddingTop: '2rem',
                    marginTop: '1rem',
                    height: '50vh',
                },
            });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();

            const container = progressbar.parentElement;
            expect(container).toBeInTheDocument();
            expect(container).toHaveClass('custom-loading-class', 'overlay', 'fullscreen');
            expect(container).toHaveStyle({
                backgroundColor: 'rgba(255, 0, 0, 0.5)',
                left: '10px',
                right: '20px',
                top: '30px',
                bottom: '40px',
                paddingTop: '2rem',
                marginTop: '1rem',
                height: '50vh',
            });
        });
    });

    describe('overlay mode', () => {
        it('renders with modal styling, custom props, and multiple style properties', () => {
            renderLoading({
                mode: 'overlay',
                style: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    height: '100vh',
                    paddingTop: '50px',
                },
                className: 'test-class',
            });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();

            const container = progressbar.parentElement;
            expect(container).toBeInTheDocument();
            expect(container).toHaveClass('test-class', 'overlay', 'modal');
            expect(container).toHaveStyle({
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                height: '100vh',
                paddingTop: '50px',
            });
        });
    });

    describe('accessibility', () => {
        it('supports custom aria-label and is indeterminate by default', () => {
            renderLoading({ 'aria-label': 'Loading data...' });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toHaveAttribute('aria-label', 'Loading data...');
            // ProgressCircle should be indeterminate (no value)
            expect(progressbar).not.toHaveAttribute('aria-valuenow');
        });
    });
});
