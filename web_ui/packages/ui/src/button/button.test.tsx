// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { darkTheme, Provider } from '@adobe/react-spectrum';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter as Router, useLocation } from 'react-router-dom';

import { Button } from './button.component';

const ThemeProvider = ({ children }: { children: ReactNode }) => {
    return <Provider theme={darkTheme}>{children}</Provider>;
};

describe('Button', () => {
    it('renders a button', async () => {
        const onPress = jest.fn();
        render(
            <ThemeProvider>
                <Router>
                    <Button onPress={onPress}>Go to annotator</Button>
                </Router>
            </ThemeProvider>
        );
        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
        fireEvent.click(button);
        expect(onPress).toHaveBeenCalled();
    });

    it('renders a button as a link when a href is used', async () => {
        const Pathname = () => {
            const location = useLocation();

            return <span aria-label='pathname'>{location.pathname}</span>;
        };
        const onPress = jest.fn();
        render(
            <ThemeProvider>
                <Router>
                    <Button href='/annotator' onPress={onPress}>
                        Go to annotator
                    </Button>
                    <Pathname />
                </Router>
            </ThemeProvider>
        );

        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
        expect(button).toHaveAttribute('href', '/annotator');
        fireEvent.click(button);
        expect(onPress).toHaveBeenCalled();
        expect(screen.getByLabelText('pathname')).toHaveTextContent('/annotator');
    });
});
