// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { useBlocker } from 'react-router-dom';

export const useHistoryBlock = (condition: boolean): [boolean, (isOpen: boolean) => void, () => void] => {
    const blocker = useBlocker(condition);

    // Reset the blocker if the user cleans the form
    useEffect(() => {
        if (blocker.state === 'blocked' && !condition) {
            blocker.reset();
        }
    }, [blocker, condition]);

    const open = blocker.state === 'blocked';
    const setOpen = (isOpen: boolean) => {
        if (blocker.state === 'blocked' && isOpen === false) {
            blocker.reset();
        }
    };
    const onUnsavedAction = () => {
        if (blocker.state === 'blocked') {
            blocker.proceed();
        }
    };

    return [open, setOpen, onUnsavedAction];
};
