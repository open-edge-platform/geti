// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useRef, useState } from 'react';

import { useEventListener } from '../event-listener/event-listener.hook';

interface UsePWAResult {
    isPWAReady: boolean;
    handlePromptInstallApp: () => Promise<boolean>;
}

export const usePWA = (): UsePWAResult => {
    const [isPWAReady, setIsPWAReady] = useState<boolean>(false);
    const promptEvent = useRef<BeforeInstallPromptEvent | null>(null);

    // This will be 'true' if the user is using Geti's standalone PWA
    const isUsingStandaloneApp = window.matchMedia('(display-mode: standalone)').matches;

    useEffect(() => {
        // We found no other way to check if the PWA is ready to be installed.
        // So this solution is based on checking if the Service Worker is registered or not
        const checkForRegisteredWorkers = async () => {
            const registeredServiceWorkers = await navigator.serviceWorker?.getRegistrations();

            const isServiceWorkerActive =
                registeredServiceWorkers?.length && registeredServiceWorkers[0].active?.state === 'activated';

            if (isServiceWorkerActive && !isUsingStandaloneApp && !isPWAReady) {
                setIsPWAReady(true);
            }
        };

        checkForRegisteredWorkers();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEventListener('beforeinstallprompt', (event: BeforeInstallPromptEvent) => {
        // Prevent Chrome 67 and earlier from automatically showing the prompt
        event.preventDefault();

        // Save the event so it can be triggered later.
        promptEvent.current = event;
        setIsPWAReady(true);
    });

    const handlePromptInstallApp = useCallback(async () => {
        if (!promptEvent.current || !promptEvent.current.prompt) {
            return false;
        }

        // Show the prompt to install PWA
        try {
            await promptEvent.current.prompt();

            const { outcome } = await promptEvent.current.userChoice;

            if (outcome === 'accepted') {
                return true;
            }
        } catch (_error) {
            // TODO: send this error to our logger or show a notification
        }

        return false;
    }, [promptEvent]);

    return { isPWAReady, handlePromptInstallApp };
};
