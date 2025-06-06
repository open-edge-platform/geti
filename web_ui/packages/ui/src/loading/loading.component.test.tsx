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

            // In inline mode, there should be no container with position absolute
            const container = progressbar.closest('[style*="position: absolute"]');
            expect(container).not.toBeInTheDocument();
        });

        it('renders with custom size', () => {
            renderLoading({ mode: 'inline', size: 'S' });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();
        });

        it('passes through custom props to ProgressCircle', () => {
            renderLoading({
                mode: 'inline',
                'aria-label': 'Custom loading message',
                value: 50
            });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toHaveAttribute('aria-label', 'Custom loading message');
        });
    });

    describe('fullscreen mode', () => {
        it('renders fullscreen loading with overlay by default', () => {
            renderLoading();

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();
            expect(progressbar).toHaveAttribute('aria-label', 'Loading...');

            // Should render overlay container with absolute positioning
            const container = progressbar.closest('[style*="position: absolute"]');
            expect(container).toBeInTheDocument();
        });

        it('renders with custom id and testid', () => {
            renderLoading({ id: 'custom-loading-id' });

            const container = screen.getByTestId('custom-loading-id');
            expect(container).toBeInTheDocument();
            expect(container).toHaveAttribute('id', 'custom-loading-id');
        });

        it('applies default background color for fullscreen mode', () => {
            renderLoading({ mode: 'fullscreen' });

            const progressbar = screen.getByRole('progressbar');
            // Find the container by traversing up the DOM tree
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({ backgroundColor: 'gray-50' });
        });

        it('applies custom background color', () => {
            renderLoading({
                mode: 'fullscreen',
                backgroundColor: 'rgba(255, 0, 0, 0.5)'
            });

            const progressbar = screen.getByRole('progressbar');
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({
                backgroundColor: 'rgba(255, 0, 0, 0.5)'
            });
        });

        it('applies positioning props', () => {
            renderLoading({
                mode: 'fullscreen',
                left: 10,
                right: 20,
                top: 30,
                bottom: 40
            });

            const progressbar = screen.getByRole('progressbar');
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({
                position: 'absolute',
                left: '10px',
                right: '20px',
                top: '30px',
                bottom: '40px'
            });
        });

        it('applies padding and margin props', () => {
            renderLoading({
                mode: 'fullscreen',
                paddingTop: '2rem',
                marginTop: '1rem'
            });

            const progressbar = screen.getByRole('progressbar');
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({
                paddingTop: '2rem',
                marginTop: '1rem'
            });
        });

        it('applies custom height for overlay', () => {
            renderLoading({
                mode: 'fullscreen',
                overlayHeight: '50vh'
            });

            const progressbar = screen.getByRole('progressbar');
            // The container (View) should have the overlayHeight
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({ height: '50vh' });
        });

        it('applies custom className', () => {
            renderLoading({
                mode: 'fullscreen',
                className: 'custom-loading-class'
            });

            const progressbar = screen.getByRole('progressbar');
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveClass('custom-loading-class');
        });
    });

    describe('overlay mode', () => {
        it('renders overlay loading with modal background', () => {
            renderLoading({ mode: 'overlay' });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();

            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({
                backgroundColor: 'var(--spectrum-alias-background-color-modal-overlay)'
            });
        });

        it('applies higher z-index for overlay mode', () => {
            renderLoading({ mode: 'overlay' });

            const progressbar = screen.getByRole('progressbar');
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({ zIndex: '20' });
        });

        it('applies default cursor style', () => {
            renderLoading({ mode: 'overlay' });

            const progressbar = screen.getByRole('progressbar');
            const container = progressbar.parentElement?.parentElement;
            expect(container).toHaveStyle({ cursor: 'default' });
        });
    });

    describe('spinner container', () => {
        it('applies custom height to spinner container', () => {
            renderLoading({
                mode: 'fullscreen',
                height: '200px'
            });

            const progressbar = screen.getByRole('progressbar');
            // The spinner's direct parent (Flex) should have the height
            const flexContainer = progressbar.parentElement;
            expect(flexContainer).toHaveStyle({ height: '200px' });
        });

        it('applies custom alignment props', () => {
            renderLoading({
                mode: 'fullscreen',
                alignItems: 'flex-start',
                justifyContent: 'flex-end'
            });

            const progressbar = screen.getByRole('progressbar');
            const flexContainer = progressbar.parentElement;
            expect(flexContainer).toHaveStyle({
                alignItems: 'flex-start',
                justifyContent: 'flex-end'
            });
        });
    });

    describe('accessibility', () => {
        it('has default aria-label', () => {
            renderLoading();

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toHaveAttribute('aria-label', 'Loading...');
        });

        it('allows custom aria-label', () => {
            renderLoading({ 'aria-label': 'Loading data...' });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toHaveAttribute('aria-label', 'Loading data...');
        });

        it('is indeterminate by default', () => {
            renderLoading();

            const progressbar = screen.getByRole('progressbar');
            // ProgressCircle should be indeterminate (no value)
            expect(progressbar).not.toHaveAttribute('aria-valuenow');
        });
    });

    describe('default props', () => {
        it('uses default values when no props are provided', () => {
            renderLoading();

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();
            expect(progressbar).toHaveAttribute('aria-label', 'Loading...');

            // Should render in fullscreen mode by default (with absolute positioning)
            const container = progressbar.closest('[style*="position: absolute"]');
            expect(container).toBeInTheDocument();
        });

        it('uses large size by default', () => {
            renderLoading();

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();
            // Default size should be 'L' based on component code
        });
    });

    describe('prop combinations', () => {
        it('handles all overlay props together', () => {
            renderLoading({
                mode: 'overlay',
                id: 'test-overlay',
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                className: 'test-class',
                height: '300px',
                overlayHeight: '100vh',
                paddingTop: '50px',
                alignItems: 'flex-start',
                justifyContent: 'center'
            });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();

            const container = screen.getByTestId('test-overlay');
            expect(container).toBeInTheDocument();
            expect(container).toHaveAttribute('id', 'test-overlay');
            expect(container).toHaveClass('test-class');
            expect(container).toHaveStyle({
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                height: '100vh',
                paddingTop: '50px',
                zIndex: '20'
            });

            // Check spinner container height and alignment
            const flexContainer = progressbar.parentElement;
            expect(flexContainer).toHaveStyle({
                height: '300px',
                alignItems: 'flex-start',
                justifyContent: 'center'
            });
        });

        it('handles inline mode with custom props', () => {
            renderLoading({
                mode: 'inline',
                size: 'M',
                height: '150px',
                alignItems: 'flex-end',
                justifyContent: 'flex-start',
                'aria-label': 'Uploading files...'
            });

            const progressbar = screen.getByRole('progressbar');
            expect(progressbar).toBeInTheDocument();
            expect(progressbar).toHaveAttribute('aria-label', 'Uploading files...');

            // Should not have overlay in inline mode
            const container = progressbar.closest('[style*="position: absolute"]');
            expect(container).not.toBeInTheDocument();

            // Check spinner container height and alignment
            const flexContainer = progressbar.parentElement;
            expect(flexContainer).toHaveStyle({
                height: '150px',
                alignItems: 'flex-end',
                justifyContent: 'flex-start'
            });
        });
    });
});
