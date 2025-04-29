// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, Suspense } from 'react';

import { useQuery } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { AxiosError } from 'axios';

import { NotificationProvider, Notifications } from '../../notification/notification.component';
import { QueryClientProvider } from './query-client-provider.component';

describe('QueryClientProvider', () => {
    afterEach(() => {
        jest.restoreAllMocks();
    });

    const wrapper = ({ children }: { children: ReactNode }) => {
        return (
            <NotificationProvider>
                <Suspense fallback={'loading...'}>
                    <QueryClientProvider defaultQueryOptions={{ queries: { retry: 0 } }}>
                        {children}
                    </QueryClientProvider>
                    <div id='custom-notification'></div>
                </Suspense>
                <Notifications />
            </NotificationProvider>
        );
    };

    it('Adds an error notifications when a query fails', async () => {
        const App = () => {
            const query = useQuery({
                queryKey: ['test'],
                queryFn: () => {
                    throw new AxiosError('An API error occured');
                },
                meta: {
                    notifyOnError: true,
                },
            });

            return <div>{query.status}</div>;
        };

        render(<App />, { wrapper });

        expect(await screen.findByText('error')).toBeInTheDocument();
        expect(screen.getByLabelText('notification toast')).toHaveTextContent('An API error occured');
    });

    it('Adds a single error notifications when a query fails in multiple components', async () => {
        const App = () => {
            const query = useQuery({
                queryKey: ['test'],
                queryFn: () => {
                    throw new AxiosError('An API error occured');
                },
                meta: {
                    notifyOnError: true,
                },
            });

            return <div>{query.status}</div>;
        };
        // ...
        render(
            <>
                <App />
                <App />
                <App />
            </>,
            { wrapper }
        );

        expect(await screen.findAllByText('error')).toHaveLength(3);
        expect(screen.getByLabelText('notification toast')).toHaveTextContent('An API error occured');
    });

    it('Ignores errors from queries not explicitely wanting to notify', async () => {
        const App = () => {
            const query = useQuery({
                queryKey: ['test'],
                queryFn: () => {
                    throw new AxiosError('An API error occured');
                },
                meta: {
                    notifyOnError: false,
                },
            });

            return <div>{query.status}</div>;
        };

        render(<App />, { wrapper });

        expect(await screen.findByText('error')).toBeInTheDocument();
        expect(screen.queryByLabelText('notification toast')).not.toBeInTheDocument();
    });

    it('Ignores non axios errors', async () => {
        const App = () => {
            const query = useQuery({
                queryKey: ['test'],
                queryFn: () => {
                    throw new Error('An API error occured');
                },
                meta: {
                    notifyOnError: true,
                },
            });

            return <div>{query.status}</div>;
        };

        render(<App />, { wrapper });

        expect(await screen.findByText('error')).toBeInTheDocument();
        expect(screen.queryByLabelText('notification toast')).not.toBeInTheDocument();
    });
});
